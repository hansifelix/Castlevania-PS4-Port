#!/usr/bin/env python3
"""Inventory undefined symbols in the public NVN/RADV relocatable object.

This is classification only. It does not resolve symbols, add stubs, or
claim that the PS4 runtime, Vulkan, WSI, or game has executed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

LINE = re.compile(r"^\\s*(?:[0-9a-fA-F]+\\s+)?([A-Za-z])\\s+(.+?)\\s*$")
WEAK_TYPES = {"w", "v"}
STRONG_TYPE = "U"
EXAMPLES_PER_CATEGORY = 12


def parse_undefined(text: str) -> dict[str, str]:
    symbols: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.endswith(":") and " " not in line:
            continue
        match = LINE.match(raw)
        if not match:
            raise ValueError(f"invalid llvm-nm undefined record: {line[:100]}")
        kind, name = match.groups()
        if kind not in ({STRONG_TYPE} | WEAK_TYPES):
            raise ValueError(f"non-undefined llvm-nm record: {line[:100]}")
        previous = symbols.get(name)
        if previous is None or (previous in WEAK_TYPES and kind == STRONG_TYPE):
            symbols[name] = kind
    return symbols


def classify(name: str) -> str:
    lower = name.lower()
    if name.startswith("nx::game::"):
        return "NX_GAME"
    if name.startswith("nx::nvn::"):
        return "NX_NVN"
    if name.startswith("nx::plat::"):
        return "NX_PLATFORM"
    if name.startswith("nx::"):
        return "NX_OTHER"
    if name.startswith(("sce", "Sce")):
        return "SCE_SDK"
    if name.startswith("vk_") or lower.startswith(("radv_", "nir_", "ac_", "aco_",
            "mesa_", "_mesa", "util_", "u_", "blake3_", "gfx", "amd_", "si_",
            "glsl_", "spirv_")):
        return "MESA_RADV"
    if name.startswith(("vk", "Vk")):
        return "VULKAN_API"
    if name.startswith(("std::", "__cxa", "__gxx", "_Unwind", "typeinfo for ",
                        "vtable for ", "operator new", "operator delete")):
        return "CXX_ABI"
    if name.startswith(("malloc", "calloc", "realloc", "free", "memcpy", "memmove",
                        "memset", "strlen", "strcmp", "strncmp", "strcpy", "strncpy",
                        "fopen", "fclose", "fread", "fwrite", "fprintf", "printf",
                        "snprintf", "vsnprintf", "pread", "pwrite", "open", "close",
                        "read", "write", "mmap", "munmap", "mprotect", "clock_gettime",
                        "nanosleep", "pthread_", "__error", "__errno_location",
                        "getenv", "setenv", "stat", "fstat", "lseek", "ftello",
                        "fseeko", "dlopen", "dlsym", "abort", "qsort", "posix_")):
        return "C_LIBC_POSIX"
    return "OTHER_EXTERNAL"


def inspect(text: str) -> dict:
    symbols = parse_undefined(text)
    groups: dict[str, list[str]] = {}
    for name in sorted(symbols):
        groups.setdefault(classify(name), []).append(name)
    categories = []
    for category in sorted(groups):
        names = groups[category]
        categories.append({
            "category": category,
            "distinct": len(names),
            "strong": sum(symbols[name] == STRONG_TYPE for name in names),
            "weak": sum(symbols[name] in WEAK_TYPES for name in names),
            "examples": names[:EXAMPLES_PER_CATEGORY],
        })
    return {
        "classification": "INVENTORY_ONLY_NOT_RESOLUTION",
        "total_undefined_distinct": len(symbols),
        "strong_undefined_distinct": sum(kind == STRONG_TYPE for kind in symbols.values()),
        "weak_undefined_distinct": sum(kind in WEAK_TYPES for kind in symbols.values()),
        "categories": categories,
        "eboot_created": False,
        "pkg_created": False,
        "ps4_vulkan_executed": False,
        "wsi_videoout_executed": False,
        "game_boot_verified": False,
        "drive_bytes_written": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--undefined", type=Path, required=True,
                        help="llvm-nm -C --undefined-only output from one relocatable object")
    args = parser.parse_args()
    try:
        report = inspect(args.undefined.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
