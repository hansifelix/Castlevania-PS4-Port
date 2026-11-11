#!/usr/bin/env python3
"""Cross-compile the 14 original baseline runtime units not already included
in the public GPU-bridge combined object. Works on pinned public upstream.
No AOT game objects, no ROMs and no commercial assets.
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "etapa189"))
from compile_missing_runtime import BASELINE_SOURCES, runtime_manifest

IN_GPU_BRIDGE = {
    "runtime/src/vk_bridge.cpp",
    "runtime/src/vk_swapchain.cpp",
    "runtime/src/vk_present.cpp",
    "runtime/src/vk_gen.cpp",
    "runtime/src/hle_vi.cpp",
}


def main():
    p = argparse.ArgumentParser()
    for x in ("upstream", "sdk", "compat", "vulkan", "out"):
        p.add_argument("--" + x, required=True, type=Path)
    args = p.parse_args()
    manifest, duplicates = runtime_manifest(
        (args.upstream / "CMakeLists.txt").read_text(encoding="utf8")
    )
    actual = set(manifest)
    if len(manifest) != 87 or not BASELINE_SOURCES.issubset(actual):
        raise RuntimeError("Upstream manifest changed: fail closed")
    remaining = sorted(BASELINE_SOURCES - IN_GPU_BRIDGE)
    if len(remaining) != 14:
        raise RuntimeError("Incorrect 19-source baseline or 5-source GPU bridge")
    args.out.mkdir(parents=True, exist_ok=True)
    sources = remaining + ["games/castlevania/game.cpp"]
    for i, rel in enumerate(sources, 1):
        filename = args.upstream / rel
        name = rel.replace("/", "_").removesuffix(".cpp")
        output = args.out / f"BASE-{name}.o"
        command = [
            "clang++-18", "--target=x86_64-pc-freebsd12-elf", "-std=c++20",
            "-O0", "-g0", "-fPIC", "-ferror-limit=10",
            "-D_POSIX_C_SOURCE=200809L", "-D_GNU_SOURCE",
            "-isysroot", str(args.sdk), "-isystem", str(args.sdk / "include"),
            "-isystem", str(args.sdk / "include/c++/v1"),
            "-I" + str(args.compat),
            "-I" + str(args.upstream / "runtime/include"),
            "-I" + str(args.upstream / "runtime/src"),
            "-I" + str(args.upstream / "games/castlevania"),
            "-I" + str(args.vulkan / "include"),
            "-include", "stdlib.h", "-c", str(filename), "-o", str(output),
        ]
        print(f"LINGSHU190_ORIGINAL_BASELINE={i}/{len(sources)}:{rel}", flush=True)
        subprocess.run(command, check=True, timeout=100)
        if not output.exists() or not output.stat().st_size:
            raise RuntimeError("Empty source object: " + rel)
    print(
        "LINGSHU190_BASELINE_14_PLUS_PUBLIC_GAME_ENTRY_1="
        "COMPILED_NO_AOT_NO_GAME_EXECUTABLE", flush=True
    )


if __name__ == "__main__":
    main()
