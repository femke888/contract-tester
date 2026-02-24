#!/usr/bin/env python
import argparse
import base64
import json
from datetime import datetime
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate signed CT1 license tokens")
    parser.add_argument("--private-key", required=True, help="Path to EC private key PEM")
    parser.add_argument("--subject", required=True, help="License owner identifier")
    parser.add_argument("--expires", required=True, help="Expiry date YYYY-MM-DD")
    parser.add_argument("--plan", default="pro", help="License plan label")
    parser.add_argument("--not-before", help="Start date YYYY-MM-DD")
    parser.add_argument("--output", help="Optional output file for token")
    args = parser.parse_args()

    key_bytes = Path(args.private_key).read_bytes()
    private_key = serialization.load_pem_private_key(key_bytes, password=None)
    if not isinstance(private_key, ec.EllipticCurvePrivateKey):
        raise ValueError("Private key must be an EC key (P-256 recommended)")

    payload = {
        "sub": args.subject,
        "exp": args.expires,
        "plan": args.plan,
        "iat": datetime.utcnow().strftime("%Y-%m-%d"),
    }
    if args.not_before:
        payload["nbf"] = args.not_before

    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64url(payload_bytes)
    signature = private_key.sign(payload_b64.encode("ascii"), ec.ECDSA(hashes.SHA256()))
    token = f"CT1.{payload_b64}.{_b64url(signature)}"

    if args.output:
        Path(args.output).write_text(token + "\n", encoding="utf-8")
    else:
        print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
