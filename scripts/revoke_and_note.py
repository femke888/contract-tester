#!/usr/bin/env python
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Set


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


def _collect_entries(args) -> List[str]:
    entries: List[str] = []
    for jti in args.jti:
        value = (jti or "").strip()
        if value:
            entries.append(value)
    for token in args.token:
        value = (token or "").strip()
        if value:
            entries.append(_token_fingerprint(value))
    for token_path in args.token_file:
        raw = Path(token_path).read_text(encoding="utf-8").strip()
        if raw:
            entries.append(_token_fingerprint(raw))
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Revoke license ids/tokens and append timestamped audit notes"
    )
    parser.add_argument(
        "--revoked-file",
        default="revoked_licenses.txt",
        help="Destination revoked list file (default: revoked_licenses.txt)",
    )
    parser.add_argument("--jti", action="append", default=[], help="Revoked license id (repeatable)")
    parser.add_argument("--token", action="append", default=[], help="Raw license token (repeatable)")
    parser.add_argument("--token-file", action="append", default=[], help="Path to file containing token")
    parser.add_argument("--reason", required=True, help="Short reason for audit trail")
    args = parser.parse_args()

    entries = _collect_entries(args)
    if not entries:
        raise SystemExit("No entries provided. Use --jti, --token, or --token-file.")

    target = Path(args.revoked_file)
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "# Revoked license entries: jti values and/or SHA-256 token fingerprints\n",
            encoding="utf-8",
        )

    existing = _read_existing(target)
    to_add = [item for item in entries if item not in existing]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with target.open("a", encoding="utf-8") as f:
        for entry in to_add:
            f.write(f"# {now} reason={args.reason}\n")
            f.write(entry + "\n")

    print(f"Added {len(to_add)} new entries to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
