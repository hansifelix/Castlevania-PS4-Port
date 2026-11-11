#!/usr/bin/env python3
"""Report real ELF64 cross-link ABI gaps without any copyrighted game data.
llvm-nm -C output comes from original public engine+GPU and PS4 adapters.
No temporary stubs, and no statement that the application boots.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def parse_nm(path: Path) -> tuple[set[str], set[str]]:
    defined: set[str] = set()
    undefined: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^(?:(?:[0-9a-fA-F]+|[-]+)\s+)?([A-Za-z])\s+(.+)$", line.strip())
        if match is None:
            continue
        kind, symbol = match.groups()
        if kind == "U":
            undefined.add(symbol)
        elif kind.upper() not in ("W", "V"):
            defined.add(symbol)
    return defined, undefined


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: audit_real_platform_symbols.py defined_nm undefined_nm", file=sys.stderr)
        return 2
    symbols, _ = parse_nm(Path(sys.argv[1]))
    _, unresolved = parse_nm(Path(sys.argv[2]))
    required = (
        "nx::plat::reserve(",
        "nx::plat::commit(",
        "nx::plat::decommit(",
        "nx::plat::log_line(",
        "nx::plat::make_dirs(",
        "nx::plat::window_size(",
        "nx::plat::screen_size(",
        "nx::boot()",
        "vk_ps4_CreateSwapchainKHR",
    )
    for name in required:
        found = any(symbol.startswith(name) for symbol in symbols)
        print(f"KAZUMA192_DEFINED_{name.partition('(')[0]}={'YES' if found else 'NO'}")
        if not found:
            raise ValueError("production implementation absent: " + name)
    platform = sorted(s for s in unresolved if s.startswith("nx::plat::"))
    runtime = sorted(s for s in unresolved if s.startswith("nx::")
                     and not s.startswith("nx::plat::"))
    native = sorted(s for s in unresolved if s.startswith("sce"))
    print(f"KAZUMA192_REMAINING_PS4_PLATFORM_SYMBOLS={len(platform)}")
    print(f"KAZUMA192_REMAINING_NX_RUNTIME_SYMBOLS={len(runtime)}")
    print(f"KAZUMA192_REMAINING_SCE_NATIVE_SYMBOLS={len(native)}")
    print(f"KAZUMA192_REMAINING_UNIQUE_EXTERNAL_SYMBOLS={len(unresolved)}")
    for sym in platform[:30]:
        print("KAZUMA192_MISSING_PS4_PLATFORM=" + sym)
    print("KAZUMA192_FULL_ENGINE_PLUS_REAL_ADAPTERS=RELOCATABLE_AUDIT_ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
