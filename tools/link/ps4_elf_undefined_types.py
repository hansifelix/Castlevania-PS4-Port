#!/usr/bin/env python3
"""Inventory ELF binding/type for undefined symbols in one relocatable object.

This reports symbol metadata only. It does not decide whether a weak import
is optional, safe to bind to zero, or accepted by create-fself.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

SYMBOL = re.compile(
    r"^\s*\d+:\s+[0-9A-Fa-f]+\s+\d+\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)(?:\s+(.*?))?\s*$"
)
MAX_EXAMPLES = 12


def inspect(text: str) -> dict:
    records: dict[tuple[str, str, str, str], None] = {}
    parsed_rows = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("Symbol table ", "Num:")):
            continue
        match = SYMBOL.match(raw)
        if not match:
            if re.match(r"^\s*\d+:", raw):
                raise ValueError(f"malformed readelf symbol row: {line[:120]}")
            continue
        kind, bind, visibility, section, name = match.groups()
        parsed_rows += 1
        if section != "UND" or bind not in {"WEAK", "GLOBAL"}:
            continue
        records[(name or "", kind, bind, visibility)] = None
    if parsed_rows == 0:
        raise ValueError("no readelf symbol rows were parsed")

    weak: dict[str, list[str]] = {}
    strong: dict[str, list[str]] = {}
    for name, kind, bind, _visibility in sorted(records):
        target = weak if bind == "WEAK" else strong
        target.setdefault(kind, []).append(name)

    def render(groups: dict[str, list[str]]) -> list[dict]:
        return [
            {"type": kind, "distinct": len(names), "examples": names[:MAX_EXAMPLES]}
            for kind, names in sorted(groups.items())
        ]

    weak_total = sum(map(len, weak.values()))
    strong_total = sum(map(len, strong.values()))
    return {
        "classification": "ELF_TYPE_INVENTORY_ONLY_NOT_SEMANTIC_VALIDATION",
        "parsed_symbol_rows": parsed_rows,
        "weak_undefined_distinct": weak_total,
        "strong_undefined_distinct": strong_total,
        "weak_undefined_by_type": render(weak),
        "strong_undefined_by_type": render(strong),
        "weak_notype_count": len(weak.get("NOTYPE", [])),
        "weak_function_count": len(weak.get("FUNC", [])),
        "weak_object_count": len(weak.get("OBJECT", [])),
        "create_fself_compatibility_proven": False,
        "weak_absent_semantics_proven": False,
        "game_boot_verified": False,
        "eboot_created": False,
        "pkg_created": False,
        "drive_bytes_written": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", type=Path, required=True,
                        help="llvm-readelf --symbols --wide output for one relocatable object")
    args = parser.parse_args()
    try:
        report = inspect(args.symbols.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
