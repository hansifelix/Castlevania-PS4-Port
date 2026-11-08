#!/usr/bin/env python3
"""Valida uniao REAL de modulos AOT via texto do llvm-nm/nm.

Nao le ROMs, NCA, NSO, codigo de jogo nem binarios: apenas os dois
relatorios de simbolos. Os testes deste script usam fixtures sinteticas.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

GUEST_DEF = re.compile(r"^\s*[0-9a-fA-F]+\s+[Tt]\s+((main|sdk|subsdk0)_[0-9A-Fa-f]+)\(nx::CPU&\)\s*$")
REQUIRED = {
    "nx_module_main",
    "nx_module_sdk",
    "nx_module_subsdk0",
    "nx::linked_modules()",
    "nx::call(nx::CPU&, unsigned long)",
    "nx::unimpl(nx::CPU&, unsigned long, char const*)",
}
GUEST_UNDEF = re.compile(r"^(main|sdk|subsdk0)_[0-9A-Fa-f]+\(nx::CPU&\)$")


def inspect(defined: Path, undefined: Path, expected: dict[str, int]) -> dict:
    found_names: dict[str, set[str]] = {x: set() for x in expected}
    defined_reqs: set[str] = set()
    for raw in defined.open(encoding="utf-8", errors="replace"):
        row = raw.strip()
        hit = GUEST_DEF.match(row)
        if hit:
            key, mod = hit.group(1), hit.group(2)
            if key in found_names[mod]:
                raise ValueError(f"duplicate guest symbol: {key}")
            found_names[mod].add(key)
        if len(row.split(maxsplit=2)) == 3:
            sym = row.split(maxsplit=2)[2]
            if sym in REQUIRED:
                defined_reqs.add(sym)

    undefs: set[str] = set()
    for raw in undefined.open(encoding="utf-8", errors="replace"):
        m = re.search(r"\bU\s+(.+)$", raw.strip())
        if m:
            undefs.add(m.group(1))
    guest_missing = sorted(x for x in undefs if GUEST_UNDEF.fullmatch(x))
    reg_missing = sorted(x for x in undefs if x.startswith("nx_module_"))
    required_missing = sorted(REQUIRED - defined_reqs)
    actual = {mod: len(found_names[mod]) for mod in expected}
    passed = (
        actual == expected
        and not guest_missing
        and not reg_missing
        and not required_missing
        and not (REQUIRED & undefs)
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "guest_function_definitions": actual,
        "expected_guest_definitions": expected,
        "total_guest_definitions": sum(actual.values()),
        "guest_undefined_count": len(guest_missing),
        "module_registration_undefined_count": len(reg_missing),
        "required_defined_missing": required_missing,
        "other_external_symbol_names_not_disclosed": len(undefs),
        "strict_link": False,
        "eboot_created": False,
        "pkg_created": False,
        "guest_semantics_verified": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--defined", type=Path, required=True)
    p.add_argument("--undefined", type=Path, required=True)
    p.add_argument("--main", type=int, default=401987)
    p.add_argument("--sdk", type=int, default=40112)
    p.add_argument("--subsdk0", type=int, default=14173)
    args = p.parse_args()
    result = inspect(args.defined, args.undefined,
                     {"main": args.main, "sdk": args.sdk, "subsdk0": args.subsdk0})
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
