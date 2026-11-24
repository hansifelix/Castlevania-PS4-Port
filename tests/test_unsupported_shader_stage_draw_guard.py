#!/usr/bin/env python3
"""Compile the exact production draw guard and prove it rejects before layout."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.link.patch_unsupported_shader_stage_failclosed import PATCHES  # noqa: E402


def main() -> int:
    compiler = (
        shutil.which("clang++-18")
        or shutil.which("clang++")
        or shutil.which("g++")
        or shutil.which("c++")
    )
    if not compiler:
        raise SystemExit("CXX_COMPILER_NOT_FOUND")

    replacement = PATCHES["runtime/src/nvn/nvn_draw.cpp"][1]
    start = replacement.find("    for (const ShaderInfo* s : *shaders) {")
    end = replacement.find("    const ShaderInfo* vs = nullptr;", start)
    if start < 0 or end <= start:
        raise SystemExit("DRAW_GUARD_PATCH_ANCHOR_DRIFT")
    guard = replacement[start:end]
    if (
        "!s || s->stage == ShaderStage::Unknown" not in guard
        or guard.count("return false;") != 1
    ):
        raise SystemExit("DRAW_GUARD_CONTRACT_MISSING")

    harness = r"""#include <vector>
enum class ShaderStage { Unknown, Vertex, Fragment, Compute };
struct ShaderInfo { ShaderStage stage; };
static int layout_calls = 0;
static void log(const char*) {}
bool simulated_draw(const std::vector<const ShaderInfo*>* shaders) {
    if (!shaders || shaders->empty()) return false;
""" + guard + r"""    ++layout_calls;
    return true;
}
int main() {
    ShaderInfo vertex{ShaderStage::Vertex}, fragment{ShaderStage::Fragment}, unknown{ShaderStage::Unknown};
    std::vector<const ShaderInfo*> bad{&vertex, &unknown, &fragment};
    if (simulated_draw(&bad) || layout_calls != 0) return 1;
    std::vector<const ShaderInfo*> null_shader{nullptr};
    if (simulated_draw(&null_shader) || layout_calls != 0) return 2;
    std::vector<const ShaderInfo*> empty;
    if (simulated_draw(&empty) || layout_calls != 0) return 3;
    std::vector<const ShaderInfo*> valid{&vertex, &fragment};
    if (!simulated_draw(&valid) || layout_calls != 1) return 4;
    return 0;
}
"""

    with tempfile.TemporaryDirectory(prefix="kazuma-etapa264-") as td:
        root = Path(td)
        source, executable = root / "draw_guard.cpp", root / "draw_guard"
        source.write_text(harness, encoding="utf-8")
        subprocess.run(
            [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(executable)],
            check=True,
        )
        subprocess.run([str(executable)], check=True)

    print("KAZUMA_ETAPA264_DRAW_STAGE_FAILCLOSED=PASS_UNSUPPORTED_AND_NULL_BEFORE_LAYOUT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
