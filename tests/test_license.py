import base64
import hashlib
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from contract_tester.license import verify_license_key


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _make_token(private_key, payload: dict) -> str:
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64url(payload_bytes)
    sig = private_key.sign(payload_b64.encode("ascii"), ec.ECDSA(hashes.SHA256()))
    return f"CT1.{payload_b64}.{_b64url(sig)}"


class TestLicense(unittest.TestCase):
    def setUp(self):
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_pem = self.private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

    def test_valid_token(self):
        future = (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
        token = _make_token(self.private_key, {"sub": "alice", "plan": "pro", "exp": future})
        with patch.dict(os.environ, {"CONTRACT_TESTER_LICENSE_PUBLIC_KEY": self.public_pem}, clear=False):
            status = verify_license_key(token)
        self.assertTrue(status["valid"])
        self.assertEqual(status["code"], "ok")

    def test_tampered_token(self):
        future = (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
        token = _make_token(self.private_key, {"sub": "alice", "plan": "pro", "exp": future})
        parts = token.split(".")
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "==").decode("utf-8"))
        payload["plan"] = "enterprise"
        tampered_payload = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        tampered = f"{parts[0]}.{tampered_payload}.{parts[2]}"

        with patch.dict(os.environ, {"CONTRACT_TESTER_LICENSE_PUBLIC_KEY": self.public_pem}, clear=False):
            status = verify_license_key(tampered)
        self.assertFalse(status["valid"])
        self.assertEqual(status["code"], "bad_signature")

    def test_expired_token(self):
        past = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        token = _make_token(self.private_key, {"sub": "alice", "plan": "pro", "exp": past})
        with patch.dict(os.environ, {"CONTRACT_TESTER_LICENSE_PUBLIC_KEY": self.public_pem}, clear=False):
            status = verify_license_key(token)
        self.assertFalse(status["valid"])
        self.assertEqual(status["code"], "expired")

    def test_not_yet_valid(self):
        future_start = (datetime.now(timezone.utc).date() + timedelta(days=3)).isoformat()
        future_end = (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
        token = _make_token(
            self.private_key,
            {"sub": "alice", "plan": "pro", "exp": future_end, "nbf": future_start},
        )
        with patch.dict(os.environ, {"CONTRACT_TESTER_LICENSE_PUBLIC_KEY": self.public_pem}, clear=False):
            status = verify_license_key(token)
        self.assertFalse(status["valid"])
        self.assertEqual(status["code"], "not_yet_valid")

    def test_malformed_token(self):
        status = verify_license_key("CT-BAD")
        self.assertFalse(status["valid"])
        self.assertEqual(status["code"], "malformed")

    def test_revoked_by_jti(self):
        future = (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
        token = _make_token(
            self.private_key, {"sub": "alice", "plan": "pro", "exp": future, "jti": "lic_123"}
        )
        with tempfile.TemporaryDirectory() as td:
            revoked = Path(td) / "revoked.txt"
            revoked.write_text("lic_123\n", encoding="utf-8")
            with patch.dict(
                os.environ,
                {
                    "CONTRACT_TESTER_LICENSE_PUBLIC_KEY": self.public_pem,
                    "CONTRACT_TESTER_REVOKED_FILE": str(revoked),
                },
                clear=False,
            ):
                status = verify_license_key(token)
        self.assertFalse(status["valid"])
        self.assertEqual(status["code"], "revoked")

    def test_revoked_by_fingerprint(self):
        future = (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
        token = _make_token(self.private_key, {"sub": "alice", "plan": "pro", "exp": future})
        token_fp = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            revoked = Path(td) / "revoked.txt"
            revoked.write_text(token_fp + "\n", encoding="utf-8")
            with patch.dict(
                os.environ,
                {
                    "CONTRACT_TESTER_LICENSE_PUBLIC_KEY": self.public_pem,
                    "CONTRACT_TESTER_REVOKED_FILE": str(revoked),
                },
                clear=False,
            ):
                status = verify_license_key(token)
        self.assertFalse(status["valid"])
        self.assertEqual(status["code"], "revoked")


if __name__ == "__main__":
    unittest.main()
