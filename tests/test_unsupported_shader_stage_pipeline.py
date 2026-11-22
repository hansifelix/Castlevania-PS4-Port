#!/usr/bin/env python3
"""Compile and exercise the exact production patch's stage_bit function."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.patch_unsupported_shader_stage_failclosed import PATCHES  # noqa: E402

PREFIX = r"""#include <cstdint>
enum class ShaderStage : uint8_t { Unknown, Vertex, Fragment, Compute };
using VkShaderStageFlags = uint32_t;
constexpr VkShaderStageFlags VK_SHADER_STAGE_VERTEX_BIT = 0x00000001;
constexpr VkShaderStageFlags VK_SHADER_STAGE_FRAGMENT_BIT = 0x00000010;
constexpr VkShaderStageFlags VK_SHADER_STAGE_COMPUTE_BIT = 0x00000020;
"""
SUFFIX = r"""
int main() {
    if (stage_bit(ShaderStage::Vertex) != VK_SHADER_STAGE_VERTEX_BIT) return 1;
    if (stage_bit(ShaderStage::Fragment) != VK_SHADER_STAGE_FRAGMENT_BIT) return 2;
    if (stage_bit(ShaderStage::Compute) != VK_SHADER_STAGE_COMPUTE_BIT) return 3;
    if (stage_bit(ShaderStage::Unknown) != 0) return 4;
    if (stage_bit(static_cast<ShaderStage>(255)) != 0) return 5;
    return 0;
}
"""


def main() -> int:
    compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++") or shutil.which("c++")
    if not compiler:
        raise SystemExit("CXX_COMPILER_NOT_FOUND")
    body = PATCHES["runtime/src/nvn/nvn_pipeline.cpp"][1]
    if body.count("stage_bit(") != 1 or "case ShaderStage::Unknown: return 0;" not in body:
        raise SystemExit("PATCH_STAGE_BIT_SOURCE_CONTRACT_FAIL")
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        src = root / "stage_bit_test.cpp"
        exe = root / "stage_bit_test"
        src.write_text(PREFIX + body + SUFFIX, encoding="utf-8")
        subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", str(src), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    print("KAZUMA_ETAPA258_STAGE_BIT_HOST=PASS_VERTEX_FRAGMENT_COMPUTE_UNKNOWN_AND_INVALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
