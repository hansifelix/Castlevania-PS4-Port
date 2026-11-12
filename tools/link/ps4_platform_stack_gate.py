#!/usr/bin/env python3
"""Fail-closed audit for the public PS4 runtime/platform object set.

The three private Castlevania AOT module tables must remain unresolved here.
A PASS means public providers are present exactly once; it is not an executable
link, EBOOT/PKG, renderer, or hardware-boot result.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

ROW = re.compile(r"^\s*(?:[0-9a-fA-F]+\s+)?([A-Za-z])\s+(.+?)\s*$")

REQUIRED = frozenset({
    "main",
    "nx::linked_modules()",
    "nx::boot()",
    "nx::game::kInfo",
    "nx::game::after_init()",
    "nx::plat::reserve(unsigned long, unsigned long)",
    "nx::plat::commit(unsigned long, unsigned long)",
    "nx::plat::decommit(unsigned long, unsigned long)",
    "nx::plat::read_pad(nx::plat::PadState&)",
    "nx::plat::create_window()",
    "nx::plat::release_window(void*)",
    "nx::plat::window_generation()",
    "nx::plat::window_minimized()",
    "nx::plat::window_size(unsigned int&, unsigned int&)",
    "nx::plat::screen_size(unsigned int&, unsigned int&)",
    "nx::plat::audio_open(void (*)(void*))",
    "nx::plat::audio_submit(void const*, unsigned long, void*)",
    "nx::plat::audio_queued()",
    "nx::plat::fopen_utf8(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, char const*)",
    "nx::plat::ftell64(_IO_FILE*)",
    "nx::plat::fseek64(_IO_FILE*, long, int)",
    "nx::plat::read_at(_IO_FILE*, long, void*, unsigned long)",
    "nx::plat::make_dirs(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&)",
    "nx::plat::monotonic_ns()",
    "nx::plat::sleep_ns(long)",
    "nx::plat::yield()",
    "nx::plat::current_thread_id()",
    "nx::plat::set_thread_name(char const*)",
    "nx::plat::start_thread(void (*)(void*), void*, unsigned long)",
    "nx::plat::exit_thread()",
    "nx::plat::exit_process(int)",
    "nx::plat::data_root()",
    "nx::plat::setting(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&)",
    "nx::plat::log_line(char const*)",
    "nx::plat::headless()",
    "nx::plat::memguard_overlap_ns(unsigned long, unsigned long)",
    "nx::plat::profile(long const*, unsigned long const* const*, unsigned long, int, std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&)",
})

PRIVATE_AOT = frozenset({
    "nx_module_main",
    "nx_module_sdk",
    "nx_module_subsdk0",
})

REAL_IMPORTS = frozenset({
    "sceVideoOutOpen",
    "sceVideoOutGetResolutionStatus",
    "sceVideoOutClose",
    "sceAudioOutInit",
    "sceAudioOutOpen",
    "sceAudioOutOutput",
    "scePadReadState",
    "sceUserServiceGetInitialUser",
    "scePthreadCreate",
    "scePthreadRename",
})


def parse_nm(text: str, *, defined: bool) -> dict[str, int]:
    result: dict[str, int] = {}
    allowed = set("ABCDGIRSTVW") if defined else {"U"}
    for line in text.splitlines():
        match = ROW.match(line)
        if not match:
            continue
        kind, symbol = match.groups()
        if kind in allowed:
            result[symbol] = result.get(symbol, 0) + 1
    return result


def inspect(defined_text: str, undefined_text: str) -> dict:
    definitions = parse_nm(defined_text, defined=True)
    undefined = parse_nm(undefined_text, defined=False)
    missing = sorted(name for name in REQUIRED if definitions.get(name, 0) != 1)
    still_undefined = sorted(name for name in REQUIRED if name in undefined)
    private_unresolved = sorted(name for name in PRIVATE_AOT if name in undefined)
    private_missing = sorted(name for name in PRIVATE_AOT if name not in undefined)
    private_invented = sorted(name for name in PRIVATE_AOT if name in definitions)
    missing_imports = sorted(name for name in REAL_IMPORTS if name not in undefined)
    status = "PASS_PUBLIC_STACK_AOT_PENDING" if not (
        missing or still_undefined or private_missing or private_invented or missing_imports
    ) else "FAIL"
    return {
        "status": status,
        "classification": "PUBLIC_PROVIDER_CLOSURE_ONLY",
        "required_public_provider_count": len(REQUIRED),
        "public_providers_missing_or_duplicated": missing,
        "public_providers_still_undefined": still_undefined,
        "private_aot_modules_still_unresolved": private_unresolved,
        "private_aot_references_missing_from_inventory": private_missing,
        "private_aot_module_definitions_forbidden": private_invented,
        "required_real_sdk_imports_missing": missing_imports,
        "strict_executable_link_passed": False,
        "aot_tables_linked": False,
        "eboot_created": False,
        "pkg_created": False,
        "ps4_hardware_tested": False,
        "game_boot_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--defined", required=True, type=Path)
    parser.add_argument("--undefined", required=True, type=Path)
    args = parser.parse_args()
    report = inspect(
        args.defined.read_text(encoding="utf-8", errors="replace"),
        args.undefined.read_text(encoding="utf-8", errors="replace"),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS_PUBLIC_STACK_AOT_PENDING" else 1


if __name__ == "__main__":
    raise SystemExit(main())
