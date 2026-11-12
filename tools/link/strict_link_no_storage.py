#!/usr/bin/env python3
"""Read-only, diskless *strict* PS4 linker diagnostic.

The linker consumes existing ELF relocatable objects and writes only to
/dev/null. No combined ELF, EBOOT, PKG, ROM/AOT or cloud output is produced.
A PASS_DRYRUN applies only to the exact input list; it is not a PS4 boot.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.etapa42.diagnosticar_link import unique_errors

MAX_EXAMPLES = 8
LIBS = ("-lc++", "-lc++abi", "-lunwind", "-lc", "-lkernel")
EXTRA_LIB_RE = re.compile(r"[A-Za-z0-9_]+\Z")


def _existing_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise ValueError(f"Missing {label}: {path.name}")
    if path.stat().st_size == 0:
        raise ValueError(f"Empty {label}: {path.name}")
    return path.resolve()


def _extra_library_flags(extra_libs: list[str] | None) -> list[str]:
    names = list(extra_libs or [])
    if any(not isinstance(name, str) or not EXTRA_LIB_RE.fullmatch(name) for name in names):
        raise ValueError("Extra library must be a plain SDK library basename")
    reserved = {item[2:] for item in LIBS} | {"m"}
    if len(names) != len(set(names)):
        raise ValueError("Duplicate extra library name")
    flags = []
    for name in names:
        if name in reserved:
            raise ValueError("Base SDK library must not be repeated as an extra library")
        flags.append("-l" + name)
    return flags


def build_command(sdk: Path, objects: list[Path], linker: str = "ld.lld-18",
                  error_limit: int = 60,
                  extra_libs: list[str] | None = None) -> list[str]:
    """Only known linker flags and existing inputs; output path is fixed to /dev/null."""
    if not 1 <= error_limit <= 100:
        raise ValueError("error_limit must be between 1 and 100")
    root = sdk.resolve()
    script = _existing_file(root / "link.x", "SDK linker script")
    crt = _existing_file(root / "lib" / "crt1.o", "SDK crt1")
    libs = root / "lib"
    if not libs.is_dir():
        raise ValueError("SDK library directory missing")
    inputs = [_existing_file(p, "existing ELF object") for p in objects]
    if not inputs:
        raise ValueError("At least one existing object is required")
    if not linker or any(ch.isspace() for ch in linker):
        raise ValueError("Invalid linker command")
    extra_flags = _extra_library_flags(extra_libs)
    cmd = [linker, "-m", "elf_x86_64", "-pie", "--no-undefined",
           "--fatal-warnings", "--script", str(script), "--eh-frame-hdr",
           f"--error-limit={error_limit}", "-L" + str(libs),
           "-o", os.devnull, str(crt)]
    cmd.extend(str(p) for p in inputs)
    cmd.extend(["--start-group", *LIBS, *extra_flags])
    if (libs / "libm.a").is_file():
        cmd.append("-lm")
    cmd.append("--end-group")
    return cmd


def summary(returncode: int, stderr: str, elapsed_ms: int, object_count: int,
            error_limit: int = 60, extra_libs: list[str] | None = None) -> dict:
    groups = unique_errors(stderr)
    return {
        "status": "PASS_DRYRUN" if returncode == 0 else "BLOCKED",
        "linker_exit_code": returncode,
        "linked_input_objects": object_count,
        "linker_elapsed_ms": elapsed_ms,
        "linker_error_limit": error_limit,
        "extra_libraries": list(extra_libs or []),
        "undefined_symbols_reported": len(groups["simbolos_indefinidos"]),
        "duplicate_symbols_reported": len(groups["simbolos_duplicados"]),
        "missing_libraries_reported": len(groups["bibliotecas_ausentes"]),
        "other_linker_errors_reported": len(groups["outros_erros"]),
        "first_undefined_symbols": groups["simbolos_indefinidos"][:MAX_EXAMPLES],
        "first_missing_libraries": groups["bibliotecas_ausentes"][:MAX_EXAMPLES],
        "first_other_errors": groups["outros_erros"][:MAX_EXAMPLES],
        "log_may_be_truncated_by_linker": True,
        "output_path": os.devnull,
        "elf_output_saved": False,
        "elf_format_verified": False,
        "eboot_created": False,
        "pkg_created": False,
        "game_boot_verified": False,
        "private_objects_uploaded": False,
        "drive_bytes_written": 0,
    }


def run(sdk: Path, objects: list[Path], linker: str, timeout: int, *,
        error_limit: int = 60, extra_libs: list[str] | None = None) -> dict:
    """Run the actual linker without ever writing a combined binary to disk."""
    cmd = build_command(sdk, objects, linker, error_limit, extra_libs)
    import time
    start = time.monotonic()
    proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, errors="replace", timeout=timeout,
                          check=False)
    elapsed = int((time.monotonic() - start) * 1000)
    return summary(proc.returncode, proc.stderr, elapsed, len(objects),
                   error_limit, extra_libs)


def main() -> int:
    p = argparse.ArgumentParser(description="Strict OpenOrbis linker diagnostic without ELF output")
    p.add_argument("--sdk", type=Path, required=True,
                   help="Existing OpenOrbis v0.5.4 toolchain root containing link.x")
    p.add_argument("--object", type=Path, action="append", required=True,
                   help="Existing ELF relocatable object; repeat to add inputs")
    p.add_argument("--linker", default="ld.lld-18")
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--error-limit", type=int, default=60)
    p.add_argument("--extra-lib", action="append", default=[],
                   help="Additional SDK library basename, without -l (repeatable)")
    a = p.parse_args()
    if a.timeout < 1 or a.timeout > 3600:
        p.error("timeout must be 1..3600 seconds")
    try:
        report = run(a.sdk, a.object, a.linker, a.timeout,
                     error_limit=a.error_limit, extra_libs=a.extra_lib)
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "ERROR", "cause": type(exc).__name__,
                          "message": str(exc)[:300], "output_saved": False},
                         ensure_ascii=False))
        return 3
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "PASS_DRYRUN" else 2


if __name__ == "__main__":
    sys.exit(main())
