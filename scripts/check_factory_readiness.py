#!/usr/bin/env python
import hashlib
import re
from pathlib import Path
from typing import List


PLACEHOLDER_PUBLIC_KEY_SHA256 = "cd0df89c6f390f3667ed1afbb63fdf20e3dcd6b7cbd641b5be77e7dda87ebc09"

REQUIRED_GITIGNORE_PATTERNS = [
    ".venv/",
    ".venv_test/",
    "build/",
    "dist/",
    "keys/",
    "license.key",
    "revoked_licenses.txt",
]


def _load_embedded_public_key(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r'DEFAULT_PUBLIC_KEY_PEM = """(.*?)"""', text, re.S)
    if not match:
        raise ValueError(f"Could not find DEFAULT_PUBLIC_KEY_PEM in {path}")
    return match.group(1)


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _check_gitignore(path: Path) -> List[str]:
    if not path.exists():
        return ["Missing .gitignore"]
    lines = {line.strip() for line in path.read_text(encoding="utf-8").splitlines()}
    issues = []
    for pattern in REQUIRED_GITIGNORE_PATTERNS:
        if pattern not in lines:
            issues.append(f".gitignore missing pattern: {pattern}")
    return issues


def main() -> int:
    root = Path(".")
    issues: List[str] = []

    issues.extend(_check_gitignore(root / ".gitignore"))

    key_text = _load_embedded_public_key(root / "src" / "contract_tester" / "license.py")
    key_fp = _fingerprint(key_text)
    if key_fp == PLACEHOLDER_PUBLIC_KEY_SHA256:
        issues.append(
            "Embedded public key still uses placeholder. Generate production keys and update license module."
        )

    private_key_path = root / "keys" / "license_private.pem"
    if private_key_path.exists():
        print(
            "WARNING: keys/license_private.pem exists in workspace. Keep it offline and out of source control."
        )

    if issues:
        print("Factory readiness check failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Factory readiness check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
