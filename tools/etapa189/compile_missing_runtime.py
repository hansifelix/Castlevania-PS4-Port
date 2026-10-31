#!/usr/bin/env python3
"""Audit full pinned upstream CMake runtime and compile missing PS4 objects.
No copyrighted game/module code is read, produced, or distributed here.
The 19 existing private-runtime objects are deliberately excluded.
"""
import argparse
import re
import subprocess
from pathlib import Path

BASELINE = (
    "guest_exception loader main memory kernel kernel_thread_control kernel_watch "
    "ipc svc_time svc_process svc_info hle_fs hle_hid hle_audio "
    "vk_bridge vk_swapchain vk_present vk_gen hle_vi"
)
BASELINE_SOURCES = {"runtime/src/" + name + ".cpp" for name in BASELINE.split()}


def runtime_manifest(cmake: str) -> tuple[list[str], list[str]]:
    match = re.search(r"set\(NX_RUNTIME_SOURCES\s+([\s\S]*?)\)\s*file\(GLOB", cmake)
    if not match:
        raise ValueError("Pinned upstream NX_RUNTIME_SOURCES block not found")
    raw = re.findall(r"runtime/src/[A-Za-z0-9_/.]+\.cpp", match.group(1))
    unique = list(dict.fromkeys(raw))
    repeated = sorted(name for name in unique if raw.count(name) > 1)
    if not unique or any(".." in x for x in unique):
        raise ValueError("unsafe or empty upstream source list")
    return unique, repeated


def run() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--upstream", type=Path, required=True)
    cli.add_argument("--sdk", type=Path)
    cli.add_argument("--compat", type=Path)
    cli.add_argument("--vulkan", type=Path)
    cli.add_argument("--out", type=Path)
    cli.add_argument("--audit-only", action="store_true")
    args = cli.parse_args()
    cmake = args.upstream / "CMakeLists.txt"
    original, duplicated = runtime_manifest(cmake.read_text(encoding="utf-8"))
    missing = [x for x in original if x not in BASELINE_SOURCES]
    if len(original) != 87 or len(missing) != 68:
        raise RuntimeError(
            f"Unexpected runtime manifest: total={len(original)} missing={len(missing)}"
        )
    print(f"LINGSHU189_UPSTREAM_RUNTIME_SOURCES={len(original)}", flush=True)
    print(f"LINGSHU189_ALREADY_IN_AOT={len(BASELINE_SOURCES)}", flush=True)
    print(f"LINGSHU189_MISSING_RUNTIME_SOURCES={len(missing)}", flush=True)
    print(f"LINGSHU189_DUPLICATE_CMAKE_ENTRIES={len(duplicated)}", flush=True)
    if args.audit_only:
        for src in missing:
            print("NEEDS_PS4_COMPILATION=" + src)
        return
    if not (args.sdk and args.compat and args.vulkan and args.out):
        cli.error("SDK, compat overlay, Vulkan headers and output are required")
    args.out.mkdir(parents=True, exist_ok=True)
    for n, src in enumerate(missing, 1):
        filename = args.upstream / src
        if not filename.is_file():
            raise FileNotFoundError(filename)
        objname = src.replace("/", "_").removesuffix(".cpp") + ".o"
        output = args.out / ("RT-" + objname)
        # Pinned upstream nvn_debug.cpp has std::max(float, double),
        # which strict OpenOrbis libc++ rejects. Patch ONLY a temporary
        # copy, with a single exact-match assertion; never change upstream.
        build_input = filename
        if src == "runtime/src/nvn/nvn_debug.cpp":
            original_text = filename.read_text(encoding="utf-8")
            before = "std::max(big, std::ldexp(float(1024 + m), int(e) - 25) * (e ? 1.0f : 0.0f))"
            after = "std::max<float>(big, std::ldexp(float(1024 + m), int(e) - 25) * (e ? 1.0f : 0.0f))"
            if original_text.count(before) != 1:
                raise RuntimeError("Pinned nvn_debug.cpp changed; aborting PS4 compat patch")
            build_input = filename.with_name("nvn_debug_ps4_189.cpp")
            build_input.write_text(original_text.replace(before, after), encoding="utf-8")
            print("LINGSHU189_NVN_DEBUG_FLOAT_TYPE=PATCHED_EXACTLY_ONCE", flush=True)
        cmd = [
            "clang++-18", "--target=x86_64-pc-freebsd12-elf",
            "-std=c++20", "-O0", "-g0", "-fPIC", "-ferror-limit=10",
            "-D_POSIX_C_SOURCE=200809L", "-D_GNU_SOURCE",
            "-isysroot", str(args.sdk),
            "-isystem", str(args.sdk / "include"),
            "-isystem", str(args.sdk / "include/c++/v1"),
            "-I" + str(args.compat),
            "-I" + str(args.upstream / "runtime/include"),
            "-I" + str(args.upstream / "runtime/src"),
            "-I" + str(args.upstream / "games/castlevania"),
            "-I" + str(args.vulkan / "include"),
            "-include", "stdlib.h",
            "-c", str(build_input), "-o", str(output),
        ]
        print(f"LINGSHU189_COMPILE={n}/{len(missing)}:{src}", flush=True)
        subprocess.run(cmd, check=True, timeout=100)
        if output.stat().st_size == 0:
            raise RuntimeError("Empty PS4 object for " + src)
    print("LINGSHU189_FULL_87_RUNTIME_OBJECTS_COMPILED_68_NEW_NO_GAME", flush=True)


if __name__ == "__main__":
    run()
