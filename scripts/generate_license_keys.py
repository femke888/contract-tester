#!/usr/bin/env python
import argparse
import re
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def _pem_text(public_bytes: bytes) -> str:
    return public_bytes.decode("utf-8").strip()


def _update_embedded_public_key(license_py: Path, public_pem: str) -> None:
    content = license_py.read_text(encoding="utf-8")
    pattern = re.compile(
        r'DEFAULT_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----.*?-----END PUBLIC KEY-----\n"""',
        re.DOTALL,
    )
    replacement = f'DEFAULT_PUBLIC_KEY_PEM = """{public_pem}\n"""'
    updated, count = pattern.subn(replacement, content, count=1)
    if count != 1:
        raise ValueError(f"Could not update DEFAULT_PUBLIC_KEY_PEM in {license_py}")
    license_py.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate EC P-256 keypair for license signing")
    parser.add_argument(
        "--private-out",
        default="keys/license_private.pem",
        help="Path to write private key PEM",
    )
    parser.add_argument(
        "--public-out",
        default="keys/license_public.pem",
        help="Path to write public key PEM",
    )
    parser.add_argument(
        "--update-license-module",
        action="store_true",
        help="Update embedded DEFAULT_PUBLIC_KEY_PEM in src/contract_tester/license.py",
    )
    parser.add_argument(
        "--license-module-path",
        default="src/contract_tester/license.py",
        help="Path to license module to update",
    )
    args = parser.parse_args()

    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    private_path = Path(args.private_out)
    public_path = Path(args.public_out)
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)

    if args.update_license_module:
        _update_embedded_public_key(Path(args.license_module_path), _pem_text(public_pem))

    print(f"Wrote private key: {private_path}")
    print(f"Wrote public key: {public_path}")
    if args.update_license_module:
        print(f"Updated embedded public key in: {args.license_module_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
