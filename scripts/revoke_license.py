#!/usr/bin/env python
import argparse
import hashlib
from pathlib import Path
from typing import Set


def _read_existing(path: Path) -> Set[str]:
    if not path.exists():
        return set()
    items: Set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        items.add(value)
    return items


def _token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Append revoked license identifiers (jti or token fingerprint)"
    )
    parser.add_argument(
        "--revoked-file",
        default="revoked_licenses.txt",
        help="Destination revoked list file (default: revoked_licenses.txt)",
    )
    parser.add_argument("--jti", action="append", default=[], help="Revoked license id (repeatable)")
    parser.add_argument("--token", action="append", default=[], help="Raw license token (repeatable)")
    parser.add_argument("--token-file", action="append", default=[], help="Path to file containing token")
    args = parser.parse_args()

    entries = []
    for jti in args.jti:
        val = (jti or "").strip()
        if val:
            entries.append(val)

    for token in args.token:
        val = (token or "").strip()
        if val:
            entries.append(_token_fingerprint(val))

    for token_path in args.token_file:
        raw = Path(token_path).read_text(encoding="utf-8").strip()
        if raw:
            entries.append(_token_fingerprint(raw))

    if not entries:
        raise SystemExit("No entries provided. Use --jti, --token, or --token-file.")

    target = Path(args.revoked_file)
    existing = _read_existing(target)
    to_add = [item for item in entries if item not in existing]

    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "# Revoked license entries: jti values and/or SHA-256 token fingerprints\n",
            encoding="utf-8",
        )

    if to_add:
        with target.open("a", encoding="utf-8") as f:
            for item in to_add:
                f.write(item + "\n")

    print(f"Added {len(to_add)} new entries to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
