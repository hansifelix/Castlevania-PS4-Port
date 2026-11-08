#!/usr/bin/env python3
"""Fail-closed PS4 boot/runtime/video partial-link audit (text only).

Verifies that real public runtime, memory, guest dispatcher, 3-module registry
and video provider definitions are present together. AOT module tables remain
unresolved by design, never synthesized in this audit.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

# Exact demangled signatures produced by llvm-nm-18 -C for the pinned x86_64 toolchain.
PROVIDERS = frozenset({
    "nx::boot()",
    "nx::memory_init()",
    "nx::call(nx::CPU&, unsigned long)",
    "nx::unimpl(nx::CPU&, unsigned long, char const*)",
    "nx::commit(unsigned long, unsigned long)",
    "nx::vm_set(unsigned long, unsigned long, unsigned int, unsigned int)",
    "nx::linked_modules()",
    "nx::game::kInfo",
    "nx::game::after_init()",
    "nx::plat::screen_size(unsigned int&, unsigned int&)",
    "nx::plat::reserve(unsigned long, unsigned long)",
    "nx::plat::commit(unsigned long, unsigned long)",
    "nx::plat::decommit(unsigned long, unsigned long)",
    "nx::kernel_init()",
    "nx::current_cpu()",
    "nx::create_main_thread(unsigned long)",
    "nx::thread_checkpoint(unsigned long)",
    "nx::backtrace(nx::CPU&)",
    "nx::handle_get(unsigned int)",
})
PROPRIETARY_MODULES = frozenset({"nx_module_main", "nx_module_sdk", "nx_module_subsdk0"})
VIDEOOUT_IMPORTS = frozenset({
    "sceVideoOutOpen", "sceVideoOutGetResolutionStatus", "sceVideoOutClose"
})
ROW = re.compile(r"^\s*(?:[0-9a-fA-F]+\s+)?([A-Za-z])\s+(.+?)\s*$")


def parse(text: str, *, defined: bool) -> dict[str, int]:
    out: dict[str, int] = {}
    kinds = set("ABCDGIRSTVW") if defined else {"U"}
    for line in text.splitlines():
        match = ROW.match(line)
        if not match:
            continue
        kind, symbol = match.groups()
        if kind not in kinds:
            continue
        out[symbol] = out.get(symbol, 0) + 1
    return out


def inspect(defined: str, undefined: str) -> dict:
    defs = parse(defined, defined=True)
    undefs = parse(undefined, defined=False)
    missing = sorted(x for x in PROVIDERS if defs.get(x) != 1)
    unresolved = sorted(x for x in PROVIDERS if x in undefs)
    unfilled = sorted(x for x in PROPRIETARY_MODULES if x not in undefs)
    invented = sorted(x for x in PROPRIETARY_MODULES if x in defs)
    video_missing = sorted(x for x in VIDEOOUT_IMPORTS if x not in undefs)
    return {
        "status": "PASS" if not (missing or unresolved or unfilled or invented or video_missing) else "FAIL",
        "required_public_provider_count": len(PROVIDERS),
        "missing_or_duplicated_providers": missing,
        "public_providers_still_undefined": unresolved,
        "proprietary_module_references_missing": unfilled,
        "proprietary_module_definitions_forbidden": invented,
        "missing_real_videoout_imports": video_missing,
        "other_unresolved_symbols": len(set(undefs) - PROVIDERS - PROPRIETARY_MODULES - VIDEOOUT_IMPORTS),
        "openorbis_partial_link_only": True,
        "strict_executable_link_passed": False,
        "aot_tables_linked": False,
        "renderer_ready": False,
        "eboot_or_pkg_created": False,
        "game_boot_tested": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--defined", required=True, type=Path)
    parser.add_argument("--undefined", required=True, type=Path)
    parser.add_argument("--json", type=Path)
    a = parser.parse_args()
    result = inspect(a.defined.read_text(encoding="utf-8"),
                     a.undefined.read_text(encoding="utf-8"))
    output = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    print(output)
    if a.json:
        a.json.write_text(output + "\n", encoding="utf-8")
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
