#!/usr/bin/env python
import argparse
import hashlib
from pathlib import Path
from typing import Iterable, List


def _iter_files(dist: Path) -> Iterable[Path]:
    for p in sorted(dist.iterdir()):
        if p.is_file() and p.name.upper() != "SHA256SUMS.TXT":
            yield p


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_checksums(dist: Path, output: Path) -> List[str]:
    lines: List[str] = []
    for p in _iter_files(dist):
        lines.append(f"{_sha256(p)}  {p.name}")
    output.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="ascii")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Write SHA-256 checksums for dist artifacts")
    parser.add_argument("--dist", default="dist", help="Distribution directory")
    parser.add_argument(
        "--output",
        help="Output checksum file path (default: <dist>/SHA256SUMS.txt)",
    )
    args = parser.parse_args()

    dist = Path(args.dist)
    if not dist.exists() or not dist.is_dir():
        raise SystemExit(f"Dist directory not found: {dist}")
    output = Path(args.output) if args.output else dist / "SHA256SUMS.txt"
    lines = write_checksums(dist, output)
    print(f"Wrote {len(lines)} checksums to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
