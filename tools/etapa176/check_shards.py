#!/usr/bin/env python3
"""Validate exactly seven AOT shards before a costly private full link.

Checks filenames, duplication, nonempty regular files, and zstd frame magic.
The private workflow MUST additionally run 'zstd -t' for frame integrity.
No commercial bytes or file contents are emitted.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

MAIN_RANGES = ((0, 284), (285, 569), (570, 854),
               (855, 1139), (1140, 1424), (1425, 1706))
MAIN_NAMES = frozenset(f"MAIN_{start}-{end}.o.zst" for start, end in MAIN_RANGES)
SDK_NAME = "sdk-subdk-aot-objects-152.o.zst"
ZSTD_MAGIC = bytes.fromhex("28b52ffd")


def check_file(path: Path) -> None:
    if path.is_symlink() or not path.is_file() or path.stat().st_size <= 8:
        raise ValueError(f"Invalid regular zstd shard: {path.name}")
    with path.open("rb") as stream:
        if stream.read(4) != ZSTD_MAGIC:
            raise ValueError(f"Invalid zstd header: {path.name}")


def validate(main_dir: Path, sdk_path: Path) -> int:
    if not main_dir.is_dir() or main_dir.is_symlink():
        raise ValueError("Missing or invalid private MAIN directory")
    # rglob includes nested subdirectories created by 'gh run download --pattern'.
    found = list(main_dir.rglob("*.o.zst"))
    names = [path.name for path in found]
    if len(found) != len(MAIN_NAMES) or set(names) != MAIN_NAMES:
        missing = sorted(MAIN_NAMES.difference(names))
        unknown = sorted(set(names).difference(MAIN_NAMES))
        raise ValueError(f"MAIN shard mismatch: missing={missing}, unexpected={unknown}, files={len(found)}")
    for path in found:
        check_file(path)
    if sdk_path.name != SDK_NAME:
        raise ValueError("Unexpected SDK+SUBSDK0 archive name")
    check_file(sdk_path)
    return len(found) + 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-dir", type=Path, required=True)
    parser.add_argument("--sdk-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        count = validate(args.main_dir, args.sdk_file)
    except (ValueError, OSError) as error:
        print(f"LINGSHU176_AOT_SHARD_CONTRACT=FAILED: {error}", file=sys.stderr)
        return 2
    print(f"LINGSHU176_AOT_SHARD_CONTRACT={count}_STRUCTURE_OK_ZSTD_TEST_REQUIRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
