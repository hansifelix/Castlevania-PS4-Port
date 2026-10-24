#!/usr/bin/env python3
"""Copy unchanged Etapa67 renderer and hook real nx::plat Vulkan bridge.

All source-code anchors are counted: fail closed if Etapa67 has changed.
The 67 renderer is never rewritten in the repository.
"""
from pathlib import Path
import sys


def replace_exact(code: str, before: str, after: str) -> str:
    n = code.count(before)
    if n != 1:
        raise ValueError(f"Expected exactly 1 occurrence of source anchor, found {n}: {before[:96]!r}")
    return code.replace(before, after, 1)


def patch(src: str) -> str:
    src = replace_exact(src, '#include "tri_frag_spv.h"',
        '#include "tri_frag_spv.h"\n'
        'extern void *kazuma68_gipa(void);\n'
        'extern const char *kazuma68_surface_extension(void);\n'
        'extern int kazuma68_create_surface(VkInstance instance, VkSurfaceKHR *surface);')
    src = replace_exact(src,
        'const char *inst_ext[] = { "VK_KHR_surface", "VK_EXT_headless_surface" };',
        'const char *inst_ext[] = { "VK_KHR_surface", kazuma68_surface_extension() };')
    src = replace_exact(src,
        '    VkInstance instance;\n'
        '    must(vkCreateInstance(&ici, NULL, &instance), "vkCreateInstance");',
        '    PFN_vkGetInstanceProcAddr get_proc = (PFN_vkGetInstanceProcAddr)kazuma68_gipa();\n'
        '    if (!get_proc) { say("KAZUMA68: NX_PLAT_GIPA_AUSENTE"); for (;;) sleep(1); }\n'
        '    PFN_vkCreateInstance create_instance = (PFN_vkCreateInstance)get_proc(VK_NULL_HANDLE, "vkCreateInstance");\n'
        '    if (!create_instance) { say("KAZUMA68: VK_CREATE_INSTANCE_AUSENTE"); for (;;) sleep(1); }\n'
        '    say("KAZUMA68: NX_PLAT_GIPA=OK");\n'
        '    VkInstance instance;\n'
        '    must(create_instance(&ici, NULL, &instance), "nx::plat::gipa->vkCreateInstance");')
    src = replace_exact(src,
        '    VkHeadlessSurfaceCreateInfoEXT hsci = { .sType = VK_STRUCTURE_TYPE_HEADLESS_SURFACE_CREATE_INFO_EXT };\n'
        '    VkSurfaceKHR surface;\n'
        '    must(vkCreateHeadlessSurfaceEXT(instance, &hsci, NULL, &surface), "vkCreateHeadlessSurfaceEXT");',
        '    VkSurfaceKHR surface = VK_NULL_HANDLE;\n'
        '    must((VkResult)kazuma68_create_surface(instance, &surface), "nx::plat::vulkan_create_surface");\n'
        '    say("KAZUMA68: NX_PLAT_SURFACE=OK; RENDER_ORBIS_WSIREAL");')
    src = replace_exact(src,
        '        .pApplicationName = "orbis-triangle",',
        '        .pApplicationName = "kazuma-runtime-bridge",')
    src = replace_exact(src,
        '    say("KAZUMA67: TRIANGULO_VULKAN_PS4_CONTINUO");',
        '    say("KAZUMA68: BRIDGE_RUNTIME_VULKAN_PS4_REAL; SEM_JOGO");')
    # All other logs are renamed, but the renderer/sync path stays unchanged.
    src = src.replace('KAZUMA67:', 'KAZUMA68:')
    return src


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit('usage: prepare_source.py INPUT_TRIANGLE_C OUTPUT_TRIANGLE_C')
    a, b = map(Path, sys.argv[1:])
    source = a.read_text(encoding='utf-8')
    output = patch(source)
    b.parent.mkdir(parents=True, exist_ok=True)
    b.write_text(output, encoding='utf-8')
    print(f'KAZUMA68: bridge instrumentado no renderizador da Etapa 67 ({len(output)} bytes)')


if __name__ == '__main__':
    main()
