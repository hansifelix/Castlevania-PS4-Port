#!/usr/bin/env python3
"""Gate the authentic PS4 vkloader.c -> RADV ICD transition.

Input: llvm-nm -C from one combined relocatable ELF with
NVN upstream, PS4 bridge, and pinned orbis-porting-kit vkloader.c.
No synthetic ICD, Mesa archive, commercial shader, or game AOT linked.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

LINE = re.compile(r"^\s*(?:[0-9a-fA-F]+\s+)?([A-Za-z])\s+(.+?)\s*$")
DEFINED_GLOBAL = set("ABCDGIRSTVW")
REQUIRED = frozenset({
    "nx::plat::ps4::vk_get_instance_proc_addr()",
    "nx::plat::vulkan_get_instance_proc_addr()",
    "nx::plat::vulkan_surface_extension()",
    "vkGetInstanceProcAddr",
    "vkCreateInstance",
    "vkEnumerateInstanceExtensionProperties",
    "vkl_resolve",
})
FUNCTION_PREFIXES = (
    "nx::plat::vulkan_create_surface(",
    "nx::nvn::gpu_submit(",
    "nx::nvn::gpu_present(",
)
ICD_ENTRY = "vk_icdGetInstanceProcAddr"


def parse(text: str, *, undefined: bool) -> dict[str, int]:
    names: dict[str, int] = {}
    for line in text.splitlines():
        m = LINE.match(line)
        if not m:
            if line.strip() and not line.strip().endswith(":"):
                raise ValueError(f"invalid llvm-nm line: {line[:90]}")
            continue
        kind, name = m.groups()
        if (kind == "U" if undefined else kind in DEFINED_GLOBAL):
            names[name] = names.get(name, 0) + 1
    return names


def inspect(defined: str, undefined: str) -> dict:
    defs = parse(defined, undefined=False)
    undefs = parse(undefined, undefined=True)
    broken = sorted(x for x in REQUIRED if defs.get(x) != 1 or x in undefs)
    for prefix in FUNCTION_PREFIXES:
        matching = [name for name in defs if name.startswith(prefix)]
        if len(matching) != 1 or matching[0] in undefs or defs[matching[0]] != 1:
            broken.append(prefix)
    valid_icd_handoff = (
        ICD_ENTRY in undefs and ICD_ENTRY not in defs and
        undefs[ICD_ENTRY] == 1 and
        "vkGetInstanceProcAddr" not in undefs
    )
    if not valid_icd_handoff:
        broken.append(ICD_ENTRY + " (must be an unresolved external RADV import)")
    status = "PASS_PARTIAL_VKLOADER_TO_ICD" if not broken else "FAIL"
    return {
        "status": status,
        "bad_or_missing_provider_names": sorted(broken),
        "actual_vkloader_frontend_defined": defs.get("vkGetInstanceProcAddr") == 1,
        "real_radv_icd_import_unresolved": valid_icd_handoff,
        "nvn_submit_present_present": not any(
            x.startswith("nx::nvn::") for x in broken
        ),
        "other_unresolved_symbol_names": len(undefs) - int(ICD_ENTRY in undefs),
        "mesa_radv_archive_linked": False,
        "strict_executable_link": False,
        "ps4_gpu_executed": False,
        "ps4_frame_visible": False,
        "pkg_or_eboot_generated": False,
        "google_drive_bytes_written": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--defined", type=Path, required=True)
    parser.add_argument("--undefined", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = inspect(args.defined.read_text(encoding="utf-8"),
                         args.undefined.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS_PARTIAL_VKLOADER_TO_ICD" else 2


if __name__ == "__main__":
    sys.exit(main())
