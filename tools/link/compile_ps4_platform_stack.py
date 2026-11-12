#!/usr/bin/env python3
"""Compile the existing native PS4 platform providers into temporary ELF objects.

This step compiles only public adapter sources. It does not load private AOT
modules, create an executable, emit an EBOOT/PKG, or access game assets.
"""
from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import subprocess
import sys

PLATFORM_SOURCES = (
    "tools/etapa50/platform_ps4_memory.cpp",
    "tools/etapa73/platform_ps4_input.cpp",
    "tools/etapa74/platform_ps4_display.cpp",
    "tools/etapa75/platform_ps4_audio.cpp",
    "src/ps4/platform_ps4_app0_config.cpp",
    "src/ps4/platform_ps4_clock_thread.cpp",
    "src/ps4/platform_ps4_file_io.cpp",
    "src/ps4/platform_ps4_thread_launch.cpp",
    "src/ps4/platform_ps4_thread_name.cpp",
    "src/ps4/platform_ps4_optional_services.cpp",
    "src/ps4/platform_ps4_sysconf.cpp",
    "src/ps4/platform_ps4_thread_atexit.cpp",
    "src/runtime_bridge/linked_modules_castlevania.cpp",
    "src/ps4/main.cpp",
)

PS4_DEFINE_SOURCES = {
    "src/ps4/platform_ps4_app0_config.cpp",
    "src/ps4/platform_ps4_clock_thread.cpp",
    "src/ps4/platform_ps4_thread_launch.cpp",
}
NATIVE_DEFINE_SOURCES = {"src/ps4/platform_ps4_thread_name.cpp"}


def object_name(source: str) -> str:
    path = PurePosixPath(source)
    if path.is_absolute() or ".." in path.parts or not source.endswith(".cpp"):
        raise ValueError("Unsafe platform source path")
    return "PS4-" + source.replace("/", "__").removesuffix(".cpp") + ".o"


def build_compile_command(
    source: Path,
    output: Path,
    *,
    sdk: Path,
    compat: Path,
    upstream: Path,
    repository: Path,
    compiler: str = "clang++-18",
) -> list[str]:
    relative = source.relative_to(repository).as_posix()
    if relative not in PLATFORM_SOURCES:
        raise ValueError(f"Source is not in the reviewed PS4 provider manifest: {relative}")

    command = [
        compiler,
        "--target=x86_64-pc-freebsd12-elf",
        "-std=c++20",
        "-O1",
        "-fPIC",
        "-ferror-limit=10",
        "-D_POSIX_C_SOURCE=200809L",
        "-D_GNU_SOURCE",
        "-isysroot", str(sdk),
        "-isystem", str(sdk / "include"),
        "-isystem", str(sdk / "include/c++/v1"),
        "-I", str(compat),
        "-I", str(upstream / "runtime/include"),
        "-I", str(upstream / "runtime/src"),
        "-I", str(upstream / "runtime/src/nvn"),
        "-I", str(repository / "tools/etapa73"),
        "-include", "algorithm",
        "-include", "stdlib.h",
    ]
    if relative in PS4_DEFINE_SOURCES:
        command.append("-DKAZUMA_PS4=1")
    if relative in NATIVE_DEFINE_SOURCES:
        command.extend(["-DKAZUMA_PS4=1", "-DKAZUMA_PS4_NATIVE=1"])
    command.extend(["-c", str(source), "-o", str(output)])
    return command


def compile_platform_stack(
    repository: Path,
    upstream: Path,
    sdk: Path,
    compat: Path,
    output_dir: Path,
    *,
    compiler: str = "clang++-18",
    timeout: int = 100,
) -> list[Path]:
    repository = repository.resolve()
    upstream = upstream.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise ValueError("Output directory must be empty; refusing to mix stale objects")

    required = (
        compat / "nx/cpu.h",
        compat / "nx/kazuma_cpu_compat.h",
        upstream / "runtime/include/nx/module.h",
        upstream / "runtime/src/platform.h",
        repository / "tools/etapa73/pad_mapping.h",
    )
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(f"Required pinned input missing: {path}")

    outputs: list[Path] = []
    for index, relative in enumerate(PLATFORM_SOURCES, 1):
        source = repository / relative
        if source.is_symlink() or not source.is_file():
            raise FileNotFoundError(f"Missing or unsafe PS4 platform source: {source}")
        output = output_dir / object_name(relative)
        print(f"KAZUMA_PS4_PROVIDER_COMPILE={index}/{len(PLATFORM_SOURCES)}:{relative}", flush=True)
        command = build_compile_command(
            source,
            output,
            sdk=sdk,
            compat=compat,
            upstream=upstream,
            repository=repository,
            compiler=compiler,
        )
        subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            check=True,
            timeout=timeout,
        )
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(f"Empty PS4 provider object produced for {relative}")
        outputs.append(output)

    if len(outputs) != 14:
        raise RuntimeError(f"Expected 14 PS4 platform objects, got {len(outputs)}")
    print("KAZUMA_PS4_PLATFORM_OBJECTS=14_COMPILED_NO_AOT_NO_GAME_ASSETS", flush=True)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile the reviewed native PS4 platform providers"
    )
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--compat", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--compiler", default="clang++-18")
    parser.add_argument("--timeout", type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 300:
        parser.error("--timeout must be between 1 and 300 seconds")
    try:
        compile_platform_stack(
            args.repository,
            args.upstream,
            args.sdk,
            args.compat,
            args.out,
            compiler=args.compiler,
            timeout=args.timeout,
        )
    except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"KAZUMA_PS4_PROVIDER_COMPILE=FAILED:{type(exc).__name__}", file=sys.stderr, flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
