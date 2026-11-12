#!/usr/bin/env python3
"""Classify a diskless strict-link result for the public PS4 stack.

This accepts the expected failure only when the *entire* remaining undefined
set is exactly the three private Castlevania AOT module tables. It never turns
that result into an executable-link success.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PRIVATE_AOT = {
    "nx_module_main",
    "nx_module_sdk",
    "nx_module_subsdk0",
}


def classify(report: dict) -> dict:
    unresolved = set(report.get("all_undefined_symbols", []))
    expected = sorted(PRIVATE_AOT)
    unexpected = sorted(unresolved - PRIVATE_AOT)
    missing_aot = sorted(PRIVATE_AOT - unresolved)

    no_other_link_errors = (
        report.get("all_duplicate_symbols", []) == []
        and report.get("all_missing_libraries", []) == []
        and report.get("all_other_errors", []) == []
        and report.get("duplicate_symbols_reported") == 0
        and report.get("missing_libraries_reported") == 0
        and report.get("other_linker_errors_reported") == 0
    )
    safe_diskless = (
        report.get("output_path") == "/dev/null"
        and report.get("elf_output_saved") is False
        and report.get("eboot_created") is False
        and report.get("pkg_created") is False
        and report.get("private_objects_uploaded") is False
        and report.get("drive_bytes_written") == 0
    )
    expected_block = (
        report.get("status") == "BLOCKED"
        and report.get("linker_exit_code") == 1
        and unresolved == PRIVATE_AOT
        and not unexpected
        and not missing_aot
        and no_other_link_errors
        and safe_diskless
    )

    if expected_block:
        return {
            "status": "PUBLIC_LINK_CLOSED_AOT_PENDING",
            "classification": "STRICT_LINK_BLOCKED_ONLY_BY_PRIVATE_AOT",
            "unresolved_private_aot": expected,
            "unexpected_unresolved_symbols": [],
            "strict_executable_link_passed": False,
            "elf_output_saved": False,
            "eboot_created": False,
            "pkg_created": False,
            "game_boot_verified": False,
            "ps4_hardware_tested": False,
            "drive_bytes_written": 0,
        }

    return {
        "status": "FAIL",
        "classification": "PUBLIC_LINK_HAS_UNEXPECTED_BLOCKERS",
        "strict_link_status": report.get("status"),
        "unresolved_private_aot": sorted(unresolved & PRIVATE_AOT),
        "unexpected_unresolved_symbols": unexpected,
        "private_aot_references_missing": missing_aot,
        "duplicate_symbols": report.get("all_duplicate_symbols", []),
        "missing_libraries": report.get("all_missing_libraries", []),
        "other_link_errors": report.get("all_other_errors", []),
        "diskless_output_confirmed": safe_diskless,
        "strict_executable_link_passed": False,
        "eboot_created": False,
        "pkg_created": False,
        "game_boot_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        raw = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({
            "status": "ERROR",
            "cause": type(exc).__name__,
            "message": str(exc)[:300],
            "strict_executable_link_passed": False,
        }, ensure_ascii=False))
        return 3

    result = classify(raw)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PUBLIC_LINK_CLOSED_AOT_PENDING" else 2


if __name__ == "__main__":
    sys.exit(main())
