#!/usr/bin/env python3
"""Presence-only audit of strong ELF imports against real OpenOrbis SDK libraries.

This is a symbol-provider inventory, not a linker result. A symbol present in
an archive/shared object may still be unusable because of visibility, ABI,
library ordering, dependencies, or linker-script rules. No binary is emitted.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Callable

SYMBOL_ROW = re.compile(
    r"^\\s*\\d+:\\s+[0-9A-Fa-f]+\\s+\\d+\\s+(\\S+)\\s+(\\S+)\\s+(\\S+)\\s+(\\S+)(?:\\s+(.*?))?\\s*$"
)
DEFINED_NM_TYPES = set("ABCDGIRSTVW")
MAX_LIBRARY_FILES = 512
MAX_EXAMPLES = 30


def parse_undefined_symbols(readelf_text: str) -> tuple[set[str], set[str]]:
    """Return (strong GLOBAL UND, weak UND), deduplicated across ELF tables."""
    strong: set[str] = set()
    weak: set[str] = set()
    parsed_rows = 0
    for raw in readelf_text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("Symbol table ", "Num:")):
            continue
        match = SYMBOL_ROW.match(raw)
        if not match:
            if re.match(r"^\\s*\\d+:", raw):
                raise ValueError(f"malformed readelf symbol row: {line[:120]}")
            continue
        _kind, binding, _visibility, section, name = match.groups()
        parsed_rows += 1
        if section != "UND" or not name:
            continue
        if binding == "GLOBAL":
            strong.add(name)
        elif binding == "WEAK":
            weak.add(name)
    if parsed_rows == 0:
        raise ValueError("no readelf symbol rows were parsed")
    weak.difference_update(strong)
    return strong, weak


def parse_nm_defined_symbols(nm_text: str) -> set[str]:
    """Parse llvm-nm --format=posix --extern-only --defined-only output."""
    symbols: set[str] = set()
    for raw in nm_text.splitlines():
        line = raw.strip()
        if not line or line.endswith(":"):
            continue
        fields = line.split()
        if len(fields) < 2:
            continue
        name, symbol_type = fields[0], fields[1]
        if len(symbol_type) != 1 or not symbol_type.isalpha():
            continue
        if symbol_type.upper() == "U":
            continue
        if symbol_type.upper() in DEFINED_NM_TYPES:
            symbols.add(name)
    return symbols


def _library_files(directories: list[Path]) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    roots: list[Path] = []
    for directory in directories:
        root = directory.resolve()
        if not root.is_dir():
            raise ValueError(f"SDK library directory missing: {directory}")
        if root not in roots:
            roots.append(root)
    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.suffix not in {".a", ".so"} or not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            label = f"{root.name}/{path.relative_to(root).as_posix()}"
            found.append((label, resolved))
    if len(found) > MAX_LIBRARY_FILES:
        raise ValueError(f"too many SDK libraries to audit: {len(found)} > {MAX_LIBRARY_FILES}")
    return found


def audit(
    readelf_text: str,
    library_directories: list[Path],
    nm: str = "llvm-nm-18",
    timeout_seconds: int = 20,
    runner: Callable = subprocess.run,
) -> dict:
    strong, weak = parse_undefined_symbols(readelf_text)
    files = _library_files(library_directories)
    providers: dict[str, list[str]] = defaultdict(list)
    scan_errors: list[dict[str, str]] = []
    scanned = 0

    for label, path in files:
        try:
            proc = runner(
                [nm, "--extern-only", "--defined-only", "--format=posix", str(path)],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            scan_errors.append({"library": label, "cause": type(exc).__name__})
            continue
        if proc.returncode != 0:
            scan_errors.append({"library": label, "cause": f"nm_exit_{proc.returncode}"})
            continue
        scanned += 1
        for symbol in parse_nm_defined_symbols(proc.stdout):
            providers[symbol].append(label)

    matched = sorted(symbol for symbol in strong if providers.get(symbol))
    unresolved = sorted(strong.difference(matched))
    ambiguous = [
        {"symbol": symbol, "providers": sorted(providers[symbol])}
        for symbol in matched if len(set(providers[symbol])) > 1
    ]
    counts = Counter()
    for symbol in matched:
        for provider in set(providers[symbol]):
            counts[provider] += 1

    return {
        "classification": "PRESENCE_ONLY_NOT_LINK_RESOLUTION",
        "status": "COMPLETE" if not scan_errors else "PARTIAL_SCAN",
        "strong_undefined_unique": len(strong),
        "weak_undefined_unique": len(weak),
        "strong_with_sdk_provider": len(matched),
        "strong_without_sdk_provider": len(unresolved),
        "strong_with_multiple_sdk_providers": len(ambiguous),
        "libraries_discovered": len(files),
        "libraries_scanned": scanned,
        "library_scan_errors": len(scan_errors),
        "scan_error_examples": scan_errors[:MAX_EXAMPLES],
        "providers_by_library": [
            {"library": name, "strong_symbols_matched": count}
            for name, count in counts.most_common(30)
        ],
        "unresolved_examples": unresolved[:MAX_EXAMPLES],
        "multiple_provider_examples": ambiguous[:20],
        "eboot_created": False,
        "pkg_created": False,
        "game_boot_verified": False,
        "drive_bytes_written": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inventory real SDK library providers for strong PS4 ELF imports"
    )
    parser.add_argument("--symbols", type=Path, required=True,
                        help="llvm-readelf --symbols --wide output from one relocatable ELF")
    parser.add_argument("--lib-dir", type=Path, action="append", required=True,
                        help="SDK library directory; repeat to scan additional real SDK directories")
    parser.add_argument("--nm", default="llvm-nm-18")
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 120:
        parser.error("--timeout must be between 1 and 120 seconds")
    try:
        report = audit(
            args.symbols.read_text(encoding="utf-8", errors="replace"),
            args.lib_dir,
            nm=args.nm,
            timeout_seconds=args.timeout,
        )
    except (OSError, ValueError) as exc:
        print(json.dumps({
            "classification": "PRESENCE_ONLY_NOT_LINK_RESOLUTION",
            "status": "ERROR",
            "cause": type(exc).__name__,
            "message": str(exc)[:300],
            "eboot_created": False,
            "pkg_created": False,
            "drive_bytes_written": 0,
        }, ensure_ascii=False))
        return 3
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    sys.exit(main())
