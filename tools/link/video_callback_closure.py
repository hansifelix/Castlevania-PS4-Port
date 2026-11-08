#!/usr/bin/env python3
"""Audit the actual joint PS4 ELF-relocatable video callback object.

Input: demangled llvm-nm --defined-only/--undefined-only text, not game files.
This gate proves callback symbol coverage and PS4 provider resolution only.
It does NOT prove final executable link, guest semantics, NVN or gameplay.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

CALLBACK_NAMES = (
    "render_resolution",
    "framebuffer_resolution",
    "depth_resolution",
    "loading_material",
    "setting_active",
    "video_defaults",
    "video_text",
    "resolution_changed",
    "supported_resolutions",
    "fullscreen_mode",
    "fullscreen",
    "video_initialize",
    "set_fullscreen_mode",
)
DIRECT_CPU = {"render_resolution", "framebuffer_resolution", "depth_resolution"}
REQUIRED_CALLBACKS = frozenset(
    f"nx_castlevania_{name}(nx::CPU&)"
    if name in DIRECT_CPU
    else f"nx_castlevania_{name}(nx::CPU&, void (*)(nx::CPU&))"
    for name in CALLBACK_NAMES
)
REQUIRED_PROVIDERS = frozenset({
    "kazuma::ps4::video::configure_native(unsigned int, unsigned int)",
    "kazuma::ps4::video::select_render(unsigned int, unsigned int)",
    "kazuma::ps4::video::ready()",
    "kazuma::ps4::video::native_size(unsigned int&, unsigned int&)",
    "kazuma::ps4::video::render_size(unsigned int&, unsigned int&)",
    "kazuma::ps4::video::refresh_video_choices(nx::CPU&, unsigned long)",
})
SYMBOL = re.compile(r"^\s*(?:[0-9a-fA-F]+\s+)?([A-Za-z])\s+(.+?)\s*$")
CALLBACK_PREFIX = "nx_castlevania_"
PROVIDER_PREFIX = "kazuma::ps4::video::"


def names(text: str, accepted: set[str]) -> Counter[str]:
    out: Counter[str] = Counter()
    for line in text.splitlines():
        match = SYMBOL.match(line)
        if match and match.group(1) in accepted:
            out[match.group(2)] += 1
    return out


def inspect(defined: str, undefined: str, *, include_videoout: bool = False) -> dict:
    defs = names(defined, {"T", "W"})
    refs = names(undefined, {"U"})
    found = {s for s in defs if s.startswith(CALLBACK_PREFIX)}
    missing = sorted(REQUIRED_CALLBACKS - found)
    unexpected = sorted(found - REQUIRED_CALLBACKS)
    duplicate = sorted(x for x in REQUIRED_CALLBACKS if defs[x] != 1 and defs[x] > 1)
    provider_missing = sorted(s for s in REQUIRED_PROVIDERS if defs[s] != 1)
    unresolved_local = sorted(s for s in refs if s.startswith((CALLBACK_PREFIX, PROVIDER_PREFIX)))
    videoout_providers = {
        "nx::game::after_init()",
        "nx::plat::screen_size(unsigned int&, unsigned int&)",
    }
    sdk_imports = {"sceVideoOutOpen", "sceVideoOutClose", "sceVideoOutGetResolutionStatus"}
    missing_videoout = sorted(
        x for x in videoout_providers if defs[x] != 1
    ) if include_videoout else []
    unresolved_videoout = sorted(
        x for x in videoout_providers if x in refs
    ) if include_videoout else []
    missing_sdk_imports = sorted(
        x for x in sdk_imports if x not in refs
    ) if include_videoout else []
    return {
        "status": "PASS" if not (missing or unexpected or duplicate or provider_missing or unresolved_local or missing_videoout or unresolved_videoout or missing_sdk_imports) else "FAIL",
        "expected_callbacks": len(REQUIRED_CALLBACKS),
        "defined_callbacks": len(found & REQUIRED_CALLBACKS),
        "missing_callbacks": missing,
        "unexpected_callbacks": unexpected,
        "duplicate_callbacks": duplicate,
        "missing_or_duplicate_providers": provider_missing,
        "unresolved_internal_callbacks_or_providers": unresolved_local,
        "missing_videoout_providers": missing_videoout,
        "unresolved_videoout_providers": unresolved_videoout,
        "missing_real_sce_videoout_imports": missing_sdk_imports,
        "videoout_stack_verified": include_videoout and not (missing_videoout or unresolved_videoout or missing_sdk_imports),
        "other_unresolved_symbols": len(set(refs) - set(unresolved_local)),
        "partial_relocatable_link": True,
        "final_executable_link": False,
        "eboot_or_pkg": False,
        "game_boot_verified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--defined", required=True, type=Path)
    parser.add_argument("--undefined", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-videoout", action="store_true")
    args = parser.parse_args()
    report = inspect(args.defined.read_text(encoding="utf-8"),
                     args.undefined.read_text(encoding="utf-8"),
                     include_videoout=args.require_videoout)
    rendered = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
