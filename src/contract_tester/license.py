import base64
import hashlib
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import NotRequired, Optional, Set, Tuple, TypedDict

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


DEMO_MAX_TRAFFIC = 25
DEMO_MAX_PATHS = 30
LICENSE_PREFIX = "CT1"

# Replace this key for production with your own P-256 public key.
DEFAULT_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEQPHe9hx05EchvtxXxT0KDfehNGAI
oLEwmJKj3r2Atv4bG0O3i6PqsmsfYaY5wOhQLNn2NqXJ6nafzqUMykRlEA==
-----END PUBLIC KEY-----
"""


class LicenseStatus(TypedDict):
    valid: bool
    code: str
    message: str
    source: Optional[str]
    key: Optional[str]
    expires_on: NotRequired[str]
    subject: NotRequired[Optional[str]]
    plan: NotRequired[Optional[str]]


def _status(valid: bool, code: str, message: str, **extra: object) -> LicenseStatus:
    out: LicenseStatus = {"valid": valid, "code": code, "message": message, "source": None, "key": None}
    for key, value in extra.items():
        out[key] = value  # type: ignore[literal-required]
    return out


def _read_key(path: Path) -> Optional[str]:
    try:
        raw = path.read_text(encoding="utf-8").strip()
        return raw or None
    except Exception:
        return None


def _license_locations() -> Tuple[Path, Path]:
    cwd_key = Path.cwd() / "license.key"
    home = Path(os.path.expanduser("~"))
    home_key = home / ".contract_tester" / "license.key"
    return cwd_key, home_key


def _revocation_locations() -> Tuple[Path, Path]:
    env_path = os.environ.get("CONTRACT_TESTER_REVOKED_FILE")
    if env_path:
        p = Path(env_path)
        return p, p
    cwd_file = Path.cwd() / "revoked_licenses.txt"
    home = Path(os.path.expanduser("~"))
    home_file = home / ".contract_tester" / "revoked_licenses.txt"
    return cwd_file, home_file


def _read_revocations(path: Path) -> Set[str]:
    try:
        items: Set[str] = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            val = line.strip()
            if not val or val.startswith("#"):
                continue
            items.add(val)
        return items
    except Exception:
        return set()


def _load_revocations() -> Set[str]:
    items: Set[str] = set()
    a, b = _revocation_locations()
    for p in (a, b):
        if p:
            items |= _read_revocations(p)
    return items


def _token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def _get_public_key_pem() -> str:
    return os.environ.get("CONTRACT_TESTER_LICENSE_PUBLIC_KEY", DEFAULT_PUBLIC_KEY_PEM)


def _load_public_key():
    raw = _get_public_key_pem().encode("utf-8")
    return serialization.load_pem_public_key(raw)


def _parse_date(value: str) -> Optional[date]:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None


def load_license_key() -> Tuple[Optional[str], Optional[str]]:
    env_key = os.environ.get("CONTRACT_TESTER_LICENSE")
    if env_key:
        return env_key.strip(), "env"

    env_path = os.environ.get("CONTRACT_TESTER_LICENSE_FILE")
    if env_path:
        key = _read_key(Path(env_path))
        if key:
            return key, "file"

    cwd_key, home_key = _license_locations()
    for path in (cwd_key, home_key):
        key = _read_key(path)
        if key:
            return key, "file"

    return None, None


def verify_license_key(key: Optional[str]) -> LicenseStatus:
    if not key:
        return _status(False, "missing_key", "No license key found. Running in demo mode.")

    token = key.strip()
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != LICENSE_PREFIX:
        return _status(False, "malformed", "License key format is invalid.")

    payload_b64 = parts[1]
    sig_b64 = parts[2]
    try:
        payload_bytes = _b64url_decode(payload_b64)
        signature = _b64url_decode(sig_b64)
    except Exception:
        return _status(False, "malformed", "License key encoding is invalid.")

    try:
        public_key = _load_public_key()
        if not isinstance(public_key, ec.EllipticCurvePublicKey):
            return _status(False, "invalid_public_key", "License verifier key is misconfigured.")
        public_key.verify(signature, payload_b64.encode("ascii"), ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        return _status(False, "bad_signature", "License signature verification failed.")
    except Exception:
        return _status(False, "invalid_public_key", "License verifier key is misconfigured.")

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        return _status(False, "invalid_payload", "License payload is invalid JSON.")

    if not isinstance(payload, dict):
        return _status(False, "invalid_payload", "License payload must be an object.")

    revoked = _load_revocations()
    token_fp = _token_fingerprint(token)
    token_id = payload.get("jti")
    if token_fp in revoked or (isinstance(token_id, str) and token_id in revoked):
        return _status(False, "revoked", "License has been revoked.")

    exp = payload.get("exp")
    if not isinstance(exp, str):
        return _status(False, "invalid_payload", "License missing required expiry date.")
    exp_date = _parse_date(exp)
    if not exp_date:
        return _status(False, "invalid_payload", "License expiry date must use YYYY-MM-DD.")

    nbf = payload.get("nbf")
    nbf_date = _parse_date(nbf) if isinstance(nbf, str) else None
    today = datetime.now(timezone.utc).date()
    if nbf and not nbf_date:
        return _status(False, "invalid_payload", "License start date must use YYYY-MM-DD.")
    if nbf_date and today < nbf_date:
        return _status(
            False,
            "not_yet_valid",
            f"License starts on {nbf_date.isoformat()}.",
            expires_on=exp_date.isoformat(),
        )
    if today > exp_date:
        return _status(
            False,
            "expired",
            f"License expired on {exp_date.isoformat()}.",
            expires_on=exp_date.isoformat(),
        )

    subject = payload.get("sub")
    plan = payload.get("plan")
    return _status(
        True,
        "ok",
        "License is valid.",
        expires_on=exp_date.isoformat(),
        subject=subject if isinstance(subject, str) else None,
        plan=plan if isinstance(plan, str) else None,
    )


def get_license_status() -> LicenseStatus:
    key, source = load_license_key()
    status = verify_license_key(key)
    status["source"] = source
    status["key"] = key if status.get("valid") is True else None
    return status
