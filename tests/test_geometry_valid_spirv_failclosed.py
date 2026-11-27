#!/usr/bin/env python3
"""Validate a real synthetic Vulkan Geometry SPIR-V module, then test fail-closed reflection."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.link.patch_unsupported_shader_stage_failclosed import apply_patch  # noqa: E402

ASM = r"""
OpCapability Shader
OpCapability Geometry
OpMemoryModel Logical GLSL450
OpEntryPoint Geometry %main "main" %position
OpExecutionMode %main Triangles
OpExecutionMode %main OutputTriangleStrip
OpExecutionMode %main OutputVertices 3
OpDecorate %position BuiltIn Position
%void = OpTypeVoid
%float = OpTypeFloat 32
%v4float = OpTypeVector %float 4
%ptr_Output_v4float = OpTypePointer Output %v4float
%position = OpVariable %ptr_Output_v4float Output
%zero = OpConstant %float 0
%one = OpConstant %float 1
%pos = OpConstantComposite %v4float %zero %zero %zero %one
%function = OpTypeFunction %void
%main = OpFunction %void None %function
%entry = OpLabel
OpStore %position %pos
OpEmitVertex
OpEndPrimitive
OpReturn
OpFunctionEnd
"""


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main() -> int:
    upstream = Path(sys.argv[1]).resolve(strict=True)
    assembler = shutil.which("spirv-as")
    validator = shutil.which("spirv-val")
    compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++") or shutil.which("c++")
    if not assembler or not validator or not compiler:
        raise SystemExit("REQUIRED_SPIRV_TOOLS_OR_CXX_MISSING")

    apply_patch(upstream)
    reflect_cpp = upstream / "runtime/src/nvn/nvn_spirv_reflect.cpp"
    include_dir = upstream / "runtime/src/nvn"
    harness = ROOT / "tests/geometry_valid_rejected.cpp"
    if not reflect_cpp.is_file() or not harness.is_file():
        raise SystemExit("PINNED_REFLECTION_SOURCE_OR_HARNESS_MISSING")

    with tempfile.TemporaryDirectory(prefix="kazuma-etapa263-") as td:
        temp = Path(td)
        assembly = temp / "geometry.spvasm"
        module = temp / "geometry.spv"
        exe = temp / "geometry-rejected"
        assembly.write_text(ASM, encoding="utf-8")
        run([assembler, "--target-env", "vulkan1.2", str(assembly), "-o", str(module)])
        run([validator, "--target-env", "vulkan1.2", str(module)])
        run([compiler, "-std=c++20", "-DNX_SHADERS_STANDALONE",
             "-I", str(include_dir), str(reflect_cpp), str(harness), "-o", str(exe)])
        run([str(exe), str(module)])

    print("KAZUMA_ETAPA263_SPIRV_VAL_GEOMETRY=VALID_VULKAN12_SYNTHETIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
