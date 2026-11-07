#!/usr/bin/env python3
"""Private AOT C++ preflight: only counters / file indices, never source excerpts."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import tarfile

CODE = re.compile(r"(?:[^/]+/)*code_(\d{3,4})\.cpp\Z")
PATTERNS = ('countl_zero', 'popcount')
MOV_SVE = re.compile(r'"mov z\d+\.[bhsd], p\d+/m, #[^"\n]+"')

def audit(archive_path: Path, *, total: int = 1707, expected_sha256: str | None = None) -> dict:
    if not 1 <= total <= 5000 or not archive_path.is_file() or archive_path.is_symlink():
        raise ValueError('Invalid archive or unit count')
    if expected_sha256:
        sha = hashlib.sha256()
        with archive_path.open('rb') as stream:
            for part in iter(lambda: stream.read(1 << 20), b''):
                sha.update(part)
        if sha.hexdigest() != expected_sha256:
            raise ValueError('Original tar SHA-256 mismatch')
    indices: set[int] = set()
    calls = Counter()
    used = {key: set() for key in PATTERNS}
    sve_units = set()
    members = 0
    with tarfile.open(archive_path, 'r:gz') as archive:
        for member in archive:
            members += 1
            if members > total + 50:
                raise ValueError('Excessive archive member count')
            if member.issym() or member.islnk() or not member.isfile():
                raise ValueError('Archive contains symlink or non-file')
            match = CODE.fullmatch(member.name)
            if not match:
                continue
            index = int(match.group(1))
            if index in indices or index >= total or member.size < 1 or member.size > 20_000_000:
                raise ValueError('Invalid or duplicate code unit')
            indices.add(index)
            content = archive.extractfile(member).read()
            if len(content) != member.size:
                raise ValueError('Truncated code unit')
            source = content.decode('utf-8')
            for pat in PATTERNS:
                count = source.count('std::' + pat + '(')
                if count:
                    calls[pat] += count
                    used[pat].add(index)
            if MOV_SVE.search(source):
                sve_units.add(index)
    if indices != set(range(total)):
        raise ValueError('Missing code units')
    return {'units_complete': len(indices), 'std_calls': dict(calls),
            'std_affected_units': {key: sorted(used[key]) for key in PATTERNS},
            'std_union_units': len(set.union(*used.values())),
            'sve_mov_units': sorted(sve_units),
            'compiled_for_ps4': False, 'strict_link': False, 'game_data_exported': False}

def main() -> None:
    parser = argparse.ArgumentParser(description='Private main AOT source preflight')
    parser.add_argument('archive', type=Path)
    parser.add_argument('--total', type=int, default=1707)
    parser.add_argument('--sha256')
    args = parser.parse_args()
    print(json.dumps(audit(args.archive, total=args.total, expected_sha256=args.sha256),
                     ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
