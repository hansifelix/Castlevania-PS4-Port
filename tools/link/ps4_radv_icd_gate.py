#!/usr/bin/env python3
"""Audit real upstream NVN -> official vkloader -> pinned Mesa/RADV ICD closure.

Input from one llvm-nm -C of a SINGLE ld.lld -r built from authentic objects.
The actual Mesa/RADV archive must be verified by caller's release SHA-256.
This checks definitions only. It does not validate a strict runnable executable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from tools.link.ps4_vkloader_icd_gate import (
    parse, REQUIRED, FUNCTION_PREFIXES, ICD_ENTRY
)

RADV_PROVIDERS = frozenset({
    "vk_icdGetInstanceProcAddr",
    "vk_icdGetPhysicalDeviceProcAddr",
    "vk_icdNegotiateLoaderICDInterfaceVersion",
})


def inspect(defined_text: str, undefined_text: str) -> dict:
    defs = parse(defined_text, undefined=False)
    undefs = parse(undefined_text, undefined=True)
    required = REQUIRED | RADV_PROVIDERS
    missing = sorted(name for name in required
                     if defs.get(name) != 1 or name in undefs)
    for prefix in FUNCTION_PREFIXES:
        matches = [x for x in defs if x.startswith(prefix)]
        if len(matches) != 1 or defs.get(matches[0]) != 1 or matches[0] in undefs:
            missing.append(prefix)
    # Old PR #123 appropriately required vk_icdGetInstanceProcAddr to be
    # UNDEFINED. Once the real RADV archive is included that becomes a failure.
    if ICD_ENTRY in undefs or defs.get(ICD_ENTRY) != 1:
        missing.append("RADV ICD entry not resolved by real archive")
    return {
        "status": "PASS_PARTIAL_RADV" if not missing else "FAIL",
        "missing_or_duplicated_real_providers": sorted(set(missing)),
        "radv_icd_entries_defined": sum(defs.get(x) == 1 and x not in undefs
                                        for x in RADV_PROVIDERS),
        "real_vulkan_loader_defined": defs.get("vkGetInstanceProcAddr") == 1,
        "unresolved_symbol_names_remain": len(undefs),
        "radv_archive_compiled_into_relocatable_elf": not missing,
        "strict_executable_link_passed": False,
        "vulkan_runtime_initialized_on_ps4": False,
        "nvn_frame_presented_on_ps4": False,
        "rom_aot_or_shaders_included": False,
        "eboot_or_pkg_created": False,
        "google_drive_bytes_written": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--defined", type=Path, required=True)
    p.add_argument("--undefined", type=Path, required=True)
    a = p.parse_args()
    try:
        r = inspect(a.defined.read_text(encoding="utf8"),
                    a.undefined.read_text(encoding="utf8"))
    except (ValueError, OSError) as exc:
        p.error(str(exc))
    print(json.dumps(r, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if r["status"] == "PASS_PARTIAL_RADV" else 2


if __name__ == "__main__":
    sys.exit(main())
