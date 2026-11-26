#!/usr/bin/env python3
"""Fail closed when pinned NVN runtime sees an unsupported SPIR-V shader stage.

This patches only a temporary upstream checkout used by the PS4 compile smoke.
It never edits user/game data and refuses source drift or symlinked inputs.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

PATCHES = {
    "runtime/src/nvn/nvn_spirv_reflect.cpp": (
        """out.stage = model == 0 ? ShaderStage::Vertex : model == 4 ? ShaderStage::Fragment
                            : model == 5 ? ShaderStage::Compute : ShaderStage::Unknown;""",
        """out.stage = model == 0 ? ShaderStage::Vertex : model == 4 ? ShaderStage::Fragment
                            : model == 5 ? ShaderStage::Compute : ShaderStage::Unknown;
                if (out.stage == ShaderStage::Unknown) return fail("unsupported SPIR-V execution model");""",
    ),
    "runtime/src/nvn/nvn_pipeline.cpp": (
        """VkShaderStageFlags stage_bit(ShaderStage s) {
    return s == ShaderStage::Vertex     ? VK_SHADER_STAGE_VERTEX_BIT
           : s == ShaderStage::Fragment ? VK_SHADER_STAGE_FRAGMENT_BIT
                                        : VK_SHADER_STAGE_COMPUTE_BIT;
}""",
        """VkShaderStageFlags stage_bit(ShaderStage s) {
    switch (s) {
        case ShaderStage::Vertex: return VK_SHADER_STAGE_VERTEX_BIT;
        case ShaderStage::Fragment: return VK_SHADER_STAGE_FRAGMENT_BIT;
        case ShaderStage::Compute: return VK_SHADER_STAGE_COMPUTE_BIT;
        case ShaderStage::Unknown: return 0;
    }
    return 0;
}""",
    ),
    "runtime/src/nvn/nvn_draw.cpp": (
        """    const ShaderInfo* vs = nullptr;
    const ShaderInfo* fs = nullptr;
    for (const ShaderInfo* s : *shaders) {""",
        """    for (const ShaderInfo* s : *shaders) {
        if (!s || s->stage == ShaderStage::Unknown) {
            log("nvn: draw rejected: unsupported shader stage");
            return false;
        }
    }
    const ShaderInfo* vs = nullptr;
    const ShaderInfo* fs = nullptr;
    for (const ShaderInfo* s : *shaders) {""",
    ),
    "runtime/src/nvn/nvn_program_bindings.h": (
        """inline const std::vector<const ShaderInfo*>* graphics_program_shaders(const StagePrograms& programs) {
    thread_local std::vector<const ShaderInfo*> result;
    result.clear();
    constexpr ShaderStage stages[] = {ShaderStage::Vertex, ShaderStage::Fragment};
    for (unsigned stage = 0; stage < 2; stage++) {
        const auto* shaders = programs[stage] ? program_shaders(programs[stage]) : nullptr;
        if (shaders) for (const auto* shader : *shaders)
            if (shader->stage == stages[stage]) { result.push_back(shader); break; }
    }
    return &result;
}""",
        """inline const std::vector<const ShaderInfo*>* graphics_program_shaders(const StagePrograms& programs) {
    thread_local std::vector<const ShaderInfo*> result;
    result.clear();
    constexpr ShaderStage stages[] = {ShaderStage::Vertex, ShaderStage::Fragment};
    for (unsigned stage = 0; stage < 2; stage++) {
        const auto* shaders = programs[stage] ? program_shaders(programs[stage]) : nullptr;
        if (shaders) for (const auto* shader : *shaders)
            if (shader->stage == stages[stage]) { result.push_back(shader); break; }
    }
    // NVN slots 2-4 are Geometry/Tessellation, unsupported by this backend.
    // Keep a null sentinel so draw() rejects instead of silently dropping a bound stage.
    for (unsigned stage = 2; stage < 5; stage++)
        if (programs[stage]) { result.push_back(nullptr); break; }
    return &result;
}""",
    ),

}

class PatchError(Exception):
    pass


def has_symlink_component(path: Path) -> bool:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            return True
    return False


def apply_patch(root: Path) -> int:
    root = Path(os.path.abspath(root))
    if has_symlink_component(root) or not root.is_dir():
        raise PatchError("UPSTREAM_ROOT_NOT_SAFE")
    real_root = root.resolve(strict=True)
    prepared = []
    for relative, (before, after) in PATCHES.items():
        path = real_root / relative
        if has_symlink_component(path) or not path.is_file():
            raise PatchError("UPSTREAM_SOURCE_NOT_SAFE")
        text = path.read_text(encoding="utf-8")
        if after in text:
            prepared.append((path, text, False))
            continue
        if text.count(before) != 1:
            raise PatchError("PINNED_SOURCE_ANCHOR_DRIFT")
        prepared.append((path, text.replace(before, after, 1), True))
    # Validate all three files before writing any of them.
    for path, text, changed in prepared:
        if changed:
            temp = path.with_name(path.name + ".kazuma258.tmp")
            if temp.exists() or temp.is_symlink():
                raise PatchError("TEMP_PATH_EXISTS")
            temp.write_text(text, encoding="utf-8")
            os.replace(temp, path)
    return sum(changed for _, _, changed in prepared)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("upstream", type=Path)
    args = parser.parse_args()
    try:
        changed = apply_patch(args.upstream)
    except (OSError, PatchError) as exc:
        reason = str(exc) if isinstance(exc, PatchError) else type(exc).__name__
        print("KAZUMA_ETAPA258_PATCH=FAILED:" + reason, flush=True)
        return 2
    print(f"KAZUMA_ETAPA258_PATCH=PASS_FILES={len(PATCHES)}_CHANGED={changed}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
