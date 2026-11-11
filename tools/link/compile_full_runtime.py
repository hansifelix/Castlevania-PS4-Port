#!/usr/bin/env python3
"""Compile the complete pinned public runtime for the PS4 ABI, without AOT/game assets.

The 87 unique CMake runtime translation units and the public Castlevania
metadata source are compiled into temporary ELF relocatable objects. This
helper never links an executable, downloads proprietary modules, or writes
artifacts outside the caller-provided temporary directory.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

BLOCK = re.compile(r"set\(NX_RUNTIME_SOURCES\s+([\s\S]*?)\)\s*file\(GLOB")
SOURCE = re.compile(r"runtime/src/[A-Za-z0-9_./]+\.cpp\Z")
NVN_DEBUG_BEFORE = (
    "std::max(big, std::ldexp(float(1024 + m), int(e) - 25) "
    "* (e ? 1.0f : 0.0f))"
)
NVN_DEBUG_AFTER = (
    "std::max<float>(big, std::ldexp(float(1024 + m), int(e) - 25) "
    "* (e ? 1.0f : 0.0f))"
)


def parse_runtime_sources(cmake_text: str, expected_count: int | None = 87):
    """Return ordered unique source paths and repeated CMake entries."""
    match = BLOCK.search(cmake_text)
    if not match:
        raise ValueError("Pinned NX_RUNTIME_SOURCES block not found")
    raw = re.findall(r"runtime/src/[A-Za-z0-9_./]+\.cpp", match.group(1))
    if not raw:
        raise ValueError("NX_RUNTIME_SOURCES contains no literal runtime source paths")
    for item in raw:
        path = PurePosixPath(item)
        if (
            path.is_absolute()
            or ".." in path.parts
            or not item.startswith("runtime/src/")
            or not item.endswith(".cpp")
        ):
            raise ValueError("Unsafe runtime source path in pinned manifest")
    counts = Counter(raw)
    unique = list(dict.fromkeys(raw))
    duplicates = sorted(name for name, count in counts.items() if count > 1)
    if expected_count is not None and len(unique) != expected_count:
        raise ValueError(
            f"Unexpected pinned runtime manifest: unique={len(unique)}, "
            f"expected={expected_count}"
        )
    return unique, duplicates


def patch_nvn_debug(source_text: str) -> str:
    """Apply the one previously verified float/double overload fix in a temp copy."""
    if source_text.count(NVN_DEBUG_BEFORE) != 1:
        raise ValueError("Pinned nvn_debug.cpp no longer matches the exact compatibility patch")
    return source_text.replace(NVN_DEBUG_BEFORE, NVN_DEBUG_AFTER)


def object_name(source: str) -> str:
    if not SOURCE.fullmatch(source):
        raise ValueError("Invalid source path")
    return "RT-" + source.replace("/", "__").removesuffix(".cpp") + ".o"


def build_compile_command(
    source: Path,
    output: Path,
    sdk: Path,
    compat: Path,
    upstream: Path,
    vulkan_include: Path,
    mesa_include: Path,
    compiler: str = "clang++-18",
) -> list[str]:
    return [
        compiler,
        "--target=x86_64-pc-freebsd12-elf",
        "-std=c++20",
        "-O0",
        "-g0",
        "-fPIC",
        "-ferror-limit=10",
        "-D_POSIX_C_SOURCE=200809L",
        "-D_GNU_SOURCE",
        "-isysroot",
        str(sdk),
        "-isystem",
        str(sdk / "include"),
        "-isystem",
        str(sdk / "include/c++/v1"),
        "-I",
        str(compat),
        "-I",
        str(upstream / "runtime/include"),
        "-I",
        str(upstream / "runtime/src"),
        "-I",
        str(upstream / "games/castlevania"),
        "-I",
        str(vulkan_include),
        "-I",
        str(mesa_include),
        "-include",
        "algorithm",
        "-include",
        "stdlib.h",
        "-c",
        str(source),
        "-o",
        str(output),
    ]


def compile_one(
    source: Path,
    output: Path,
    sdk: Path,
    compat: Path,
    upstream: Path,
    vulkan_include: Path,
    mesa_include: Path,
    compiler: str,
    timeout: int,
) -> None:
    if source.is_symlink() or not source.is_file():
        raise FileNotFoundError(f"Missing or unsafe pinned source: {source}")
    build_input = source
    if source.as_posix().endswith("/runtime/src/nvn/nvn_debug.cpp"):
        patched_dir = output.parent / "_compat"
        patched_dir.mkdir(parents=True, exist_ok=True)
        build_input = patched_dir / "nvn_debug_ps4.cpp"
        original = source.read_text(encoding="utf-8")
        build_input.write_text(patch_nvn_debug(original), encoding="utf-8")
        print("KAZUMA_FULL_RUNTIME_NVN_DEBUG=EXACT_TEMPORARY_FLOAT_PATCH", flush=True)

    command = build_compile_command(
        build_input, output, sdk, compat, upstream,
        vulkan_include, mesa_include, compiler,
    )
    subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        check=True,
        timeout=timeout,
    )
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"Empty PS4 object produced for {source.name}")


def compile_full_runtime(
    upstream: Path,
    sdk: Path,
    compat: Path,
    vulkan_include: Path,
    mesa_include: Path,
    output_dir: Path,
    compiler: str = "clang++-18",
    timeout: int = 100,
) -> list[Path]:
    upstream = upstream.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise ValueError("Output directory must be empty; refusing to mix stale objects")
    required = (
        upstream / "CMakeLists.txt",
        compat / "nx/cpu.h",
        compat / "nx/kazuma_cpu_compat.h",
        vulkan_include / "vulkan/vulkan.h",
        mesa_include / "vulkan/vulkan.h",
    )
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(f"Required pinned build input missing: {path}")

    sources, duplicates = parse_runtime_sources(
        (upstream / "CMakeLists.txt").read_text(encoding="utf-8"),
        expected_count=87,
    )
    print(f"KAZUMA_FULL_RUNTIME_SOURCE_UNIQUE={len(sources)}", flush=True)
    print(f"KAZUMA_FULL_RUNTIME_CMAKE_DUPLICATE_ENTRIES={len(duplicates)}", flush=True)
    for name in duplicates:
        print("KAZUMA_FULL_RUNTIME_DEDUPLICATED=" + name, flush=True)

    outputs: list[Path] = []
    for index, relative in enumerate(sources, 1):
        source = upstream / relative
        output = output_dir / object_name(relative)
        print(
            f"KAZUMA_FULL_RUNTIME_COMPILE={index}/{len(sources)}:{relative}",
            flush=True,
        )
        compile_one(
            source, output, sdk, compat, upstream,
            vulkan_include, mesa_include, compiler, timeout,
        )
        outputs.append(output)

    game_source = upstream / "games/castlevania/game.cpp"
    game_output = output_dir / "GAME-castlevania.o"
    print("KAZUMA_FULL_RUNTIME_COMPILE_GAME_METADATA=games/castlevania/game.cpp", flush=True)
    compile_one(
        game_source, game_output, sdk, compat, upstream,
        vulkan_include, mesa_include, compiler, timeout,
    )
    outputs.append(game_output)
    if len(outputs) != 88:
        raise RuntimeError(f"Expected 88 public runtime/metadata objects, got {len(outputs)}")
    print("KAZUMA_FULL_RUNTIME_OBJECTS=88_COMPILED_PS4_ELF_NO_AOT_NO_GAME_DATA", flush=True)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile all 87 pinned public runtime sources plus Castlevania metadata for PS4"
    )
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--compat", type=Path, required=True)
    parser.add_argument("--vulkan", type=Path, required=True,
                        help="Pinned Khronos Vulkan-Headers include directory")
    parser.add_argument("--mesa", type=Path, required=True,
                        help="Paired Mesa Vulkan include directory")
    parser.add_argument("--out", type=Path, required=True,
                        help="Fresh temporary output directory")
    parser.add_argument("--compiler", default="clang++-18")
    parser.add_argument("--timeout", type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 300:
        parser.error("--timeout must be 1..300 seconds")
    try:
        compile_full_runtime(
            args.upstream, args.sdk, args.compat, args.vulkan,
            args.mesa, args.out, args.compiler, args.timeout,
        )
    except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(
            f"KAZUMA_FULL_RUNTIME_COMPILE=FAILED:{type(exc).__name__}",
            file=sys.stderr,
            flush=True,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
