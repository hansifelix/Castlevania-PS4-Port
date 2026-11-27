#!/usr/bin/env python3
"""Exercise the production shader-slot selector and draw guard as one path."""
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
static int layout_calls = 0;
static int override_calls = 0;
static int gather_calls = 0;
static int fragment_seen = 0;
static void log(const char*) {}
static void debug_shader_overrides(const std::vector<const ShaderInfo*>* shaders, const ShaderInfo* fs) {
    (void)shaders;
    ++override_calls;
    if (fs == &fragment) ++fragment_seen;
}
static void program_layout(const std::vector<const ShaderInfo*>&) { ++layout_calls; }
static void gather_textures(const std::vector<const ShaderInfo*>&) { ++gather_calls; }
"""

def main() -> int:
    compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++") or shutil.which("c++")
    if not compiler:
        raise SystemExit("CXX_COMPILER_NOT_FOUND")

    selector = PATCHES["runtime/src/nvn/nvn_program_bindings.h"][1]
    draw_patch = PATCHES["runtime/src/nvn/nvn_draw.cpp"][1]
    start = draw_patch.find("    for (const ShaderInfo* s : *shaders) {")
    end = draw_patch.find("    const ShaderInfo* vs = nullptr;", start)
    if start < 0 or end <= start:
        raise SystemExit("DRAW_GUARD_PATCH_ANCHOR_DRIFT")
    guard = draw_patch[start:end]
    if "if (!s || s->stage == ShaderStage::Unknown)" not in guard:
        raise SystemExit("DRAW_GUARD_CONTRACT_MISSING")

    harness = PREAMBLE + selector + r"""
bool simulated_draw(const StagePrograms& programs) {
    const auto* shaders = graphics_program_shaders(programs);
    if (!shaders || shaders->empty()) return false;
""" + guard + r"""
    const ShaderInfo* vs = nullptr;
    const ShaderInfo* fs = nullptr;
    for (const ShaderInfo* s : *shaders) {
        if (s->stage == ShaderStage::Vertex) vs = s;
        if (s->stage == ShaderStage::Fragment) fs = s;
    }
    if (!vs) return false;
    debug_shader_overrides(shaders, fs);
    program_layout(*shaders);
    gather_textures(*shaders);
    return true;
}
int main() {
    StagePrograms normal;
    normal.slots[0] = 1; normal.slots[1] = 2;
    if (!simulated_draw(normal) || layout_calls != 1 || override_calls != 1 || gather_calls != 1 || fragment_seen != 1) return 1;

    for (size_t unsupported = 2; unsupported <= 4; ++unsupported) {
        StagePrograms bad = normal;
        bad.slots[unsupported] = 3;
        if (simulated_draw(bad)) return int(unsupported);
        if (layout_calls != 1 || override_calls != 1 || gather_calls != 1 || fragment_seen != 1) return 10 + int(unsupported);
    }

    StagePrograms compute_separate = normal;
    compute_separate.slots[5] = 3;
    if (!simulated_draw(compute_separate) || layout_calls != 2 || override_calls != 2 || gather_calls != 2 || fragment_seen != 2) return 20;

    StagePrograms fragment_only;
    fragment_only.slots[1] = 2;
    if (simulated_draw(fragment_only) || layout_calls != 2 || override_calls != 2 || gather_calls != 2 || fragment_seen != 2) return 21;

    StagePrograms empty;
    if (simulated_draw(empty) || layout_calls != 2 || override_calls != 2 || gather_calls != 2 || fragment_seen != 2) return 22;
    return 0;
}
"""
    with tempfile.TemporaryDirectory(prefix="kazuma-etapa266-") as td:
        root = Path(td)
        source, executable = root / "shader_stage_path.cpp", root / "shader_stage_path"
        source.write_text(harness, encoding="utf-8")
        subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(executable)], check=True)
        subprocess.run([str(executable)], check=True)
    print("KAZUMA_ETAPA266_SELECTOR_AND_DRAW_GUARD=PASS_UNSUPPORTED_BOUND_STAGES_REJECT_BEFORE_LAYOUT_OVERRIDE_GATHER")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
