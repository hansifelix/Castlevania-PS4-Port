#!/usr/bin/env python3
"""Run the strict PS4 link diagnostic with every linker error enabled.

The command is built by the existing validated diskless helper, then only
its numeric --error-limit is changed from 100 to 0 (LLD's documented
unlimited mode). Output remains /dev/null; the full undefined-symbol list
is emitted as JSON for diagnosis. No ELF/EBOOT/PKG is saved.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.etapa42.diagnosticar_link import unique_errors
from tools.link.strict_link_no_storage import build_command, summary


def run_unlimited(
    sdk: Path,
    objects: list[Path],
    linker: str = "ld.lld-18",
    timeout: int = 900,
    extra_libs: list[str] | None = None,
) -> dict:
    command = build_command(
        sdk,
        objects,
        linker=linker,
        error_limit=100,
        extra_libs=extra_libs,
    )
    flag = command.index("--error-limit=100")
    command[flag] = "--error-limit=0"

    started = time.monotonic()
    proc = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
        check=False,
    )
    elapsed_ms = int((time.monotonic() - started) * 1000)
    groups = unique_errors(proc.stderr)
    report = summary(
        proc.returncode,
        proc.stderr,
        elapsed_ms,
        len(objects),
        error_limit=0,
        extra_libs=extra_libs,
    )
    report["log_may_be_truncated_by_linker"] = False
    report["all_undefined_symbols"] = groups["simbolos_indefinidos"]
    report["all_duplicate_symbols"] = groups["simbolos_duplicados"]
    report["all_missing_libraries"] = groups["bibliotecas_ausentes"]
    report["all_other_errors"] = groups["outros_erros"]
    report["full_diagnostic_list_truncated"] = False
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Strict OpenOrbis PS4 link with unlimited diagnostics and /dev/null output"
    )
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--object", type=Path, action="append", required=True)
    parser.add_argument("--linker", default="ld.lld-18")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--extra-lib", action="append", default=[])
    args = parser.parse_args()
    if args.timeout < 1 or args.timeout > 3600:
        parser.error("timeout must be 1..3600 seconds")
    try:
        report = run_unlimited(
            args.sdk,
            args.object,
            linker=args.linker,
            timeout=args.timeout,
            extra_libs=args.extra_lib,
        )
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({
            "status": "ERROR",
            "cause": type(exc).__name__,
            "message": str(exc)[:300],
            "output_saved": False,
            "eboot_created": False,
            "pkg_created": False,
            "drive_bytes_written": 0,
        }, ensure_ascii=False))
        return 3
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "PASS_DRYRUN" else 2


if __name__ == "__main__":
    sys.exit(main())
