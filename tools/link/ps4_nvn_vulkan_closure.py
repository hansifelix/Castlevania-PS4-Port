#!/usr/bin/env python3
"""Audit actual OpenOrbis NVN/Vulkan partial-link symbol closure (text only).

Checks both halves of the platform Vulkan loader and the real upstream NVN
submit/present implementation. The backend is NOT ready until a real RADV
loader resolves vkGetInstanceProcAddr and a strict executable link passes.
"""
import argparse
import json
from pathlib import Path
import re
import sys

LINE = re.compile(r"^\\s*(?:[0-9a-fA-F]+\\s+)?([A-Za-z])\\s+(.+?)\\s*$")
REQUIRED = frozenset({
    "nx::plat::ps4::vk_get_instance_proc_addr()",
    "nx::plat::vulkan_get_instance_proc_addr()",
    "nx::plat::vulkan_surface_extension()",
})
CREATES = ("nx::plat::vulkan_create_surface(",)
NVN_CORE = ("nx::nvn::gpu_present(", "nx::nvn::gpu_submit(")


def parse(text: str, kind: str) -> dict[str, int]:
    symbols = {}
    for line in text.splitlines():
        match = LINE.match(line)
        if not match:
            continue
        t, name = match.groups()
        if (kind == "defined" and t in "ABCDGIRSTVW") or (kind == "undefined" and t == "U"):
            symbols[name] = symbols.get(name, 0) + 1
    return symbols


def inspect(defined: str, undefined: str) -> dict:
    defs = parse(defined, "defined")
    undefs = parse(undefined, "undefined")
    missing = sorted(x for x in REQUIRED if defs.get(x) != 1 or x in undefs)
    # Demangled spellings vary by upstream signature; guard by unambiguous
    # function prefix and exact count to detect accidentally excluded source.
    for prefix in (*CREATES, *NVN_CORE):
        matching = [n for n in defs if n.startswith(prefix)]
        if len(matching) != 1 or any(n in undefs for n in matching):
            missing.append(prefix)
    # Require an ACTUAL external Vulkan implementation, not a fake provider
    # defined inside this small public bridge. The full executable must
    # resolve it against the real pinned RADV/vkloader bundle later.
    vulkan_import = "vkGetInstanceProcAddr"
    external_loader = vulkan_import in undefs and vulkan_import not in defs
    return {
        "status": "PASS_PARTIAL" if not missing and external_loader else "FAIL",
        "missing_or_ambiguous_providers": sorted(missing),
        "real_vulkan_loader_import_present": external_loader,
        "new_providers_defined": len(REQUIRED) + len(CREATES) + len(NVN_CORE) - len(missing),
        "total_external_symbol_names": len(undefs),
        "strict_gpu_link": False,
        "mesa_radv_linked": False,
        "nvn_runtime_executed": False,
        "ps4_frame_presented": False,
        "eboot_or_pkg": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--defined", type=Path, required=True)
    p.add_argument("--undefined", type=Path, required=True)
    a = p.parse_args()
    report = inspect(a.defined.read_text(encoding="utf8"),
                     a.undefined.read_text(encoding="utf8"))
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    if report["status"] != "PASS_PARTIAL":
        sys.exit(1)


if __name__ == "__main__":
    main()
