#!/usr/bin/env python3
"""Compile the exact patched graphics-stage selector and verify unsupported bound slots fail closed."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.link.patch_unsupported_shader_stage_failclosed import PATCHES  # noqa: E402

PREAMBLE = r"""#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>
enum class ShaderStage : uint8_t { Unknown, Vertex, Fragment, Compute };
struct ShaderInfo { ShaderStage stage; };
struct StagePrograms {
    std::array<uint64_t, 6> slots{};
    uint64_t operator[](size_t stage) const { return slots[stage]; }
};
static const ShaderInfo vertex{ShaderStage::Vertex};
static const ShaderInfo fragment{ShaderStage::Fragment};
static const std::vector<const ShaderInfo*> vertex_program{&vertex};
static const std::vector<const ShaderInfo*> fragment_program{&fragment};
static const std::vector<const ShaderInfo*> empty_program{};
const std::vector<const ShaderInfo*>* program_shaders(uint64_t id) {
    if (id == 1) return &vertex_program;
    if (id == 2) return &fragment_program;
    if (id == 3) return &empty_program;
    return nullptr;
}
"""

def main() -> int:
    compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++") or shutil.which("c++")
    if not compiler:
        raise SystemExit("CXX_COMPILER_NOT_FOUND")
    source = PATCHES["runtime/src/nvn/nvn_program_bindings.h"][1]
    if source.count("graphics_program_shaders(") != 1:
        raise SystemExit("PATCH_GRAPHICS_SELECTOR_ANCHOR_DRIFT")
    if "for (unsigned stage = 2; stage < 5; stage++)" not in source or "result.push_back(nullptr)" not in source:
        raise SystemExit("UNSUPPORTED_GRAPHICS_SLOT_SENTINEL_MISSING")
    harness = PREAMBLE + source + r"""
int main() {
    StagePrograms normal;
    normal.slots[0] = 1; normal.slots[1] = 2;
    auto* result = graphics_program_shaders(normal);
    if (!result || result->size() != 2 || (*result)[0] != &vertex || (*result)[1] != &fragment) return 1;

    for (size_t unsupported = 2; unsupported <= 4; ++unsupported) {
        StagePrograms bad = normal;
        bad.slots[unsupported] = 3;
        result = graphics_program_shaders(bad);
        if (!result || result->size() != 3 || (*result)[2] != nullptr) return int(unsupported);
    }

    StagePrograms compute;
    compute.slots[0] = 1; compute.slots[1] = 2; compute.slots[5] = 3;
    result = graphics_program_shaders(compute);
    if (!result || result->size() != 2 || (*result)[0] != &vertex || (*result)[1] != &fragment) return 6;

    StagePrograms empty;
    result = graphics_program_shaders(empty);
    if (!result || !result->empty()) return 7;
    return 0;
}
"""
    with tempfile.TemporaryDirectory(prefix="kazuma-etapa265-") as td:
        root = Path(td)
        src, exe = root / "graphics_slots.cpp", root / "graphics_slots"
        src.write_text(harness, encoding="utf-8")
        subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", str(src), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    print("KAZUMA_ETAPA265_GRAPHICS_SLOTS=PASS_VS_FS_REJECT_GEOMETRY_TESS_COMPUTE_IGNORED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
