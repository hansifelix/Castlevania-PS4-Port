#!/usr/bin/env python3
"""Auditoria ESTÁTICA: contrato Vulkan NVN de Castlevania x backend WSI do SMW PS4.

Não executa o jogo, não acessa NSP/APK/chaves e não valida GPU do console.
"""
import argparse
import json
import re
from pathlib import Path

CALLBACKS = (
    'vulkan_get_instance_proc_addr',
    'vulkan_surface_extension',
    'vulkan_create_surface',
)
EXTRA_PLATFORM = (
    'create_window', 'release_window', 'window_generation', 'window_minimized',
    'window_size', 'desktop_size', 'screen_size',
)


def extracted_additions(patch: str, path: str) -> str:
    """Obtém apenas linhas adicionadas de UM arquivo de diff Git unificado."""
    marker = f'diff --git a/{path} b/{path}'
    start = patch.find(marker)
    if start < 0:
        return ''
    end = patch.find('\ndiff --git ', start + len(marker))
    section = patch[start: end if end >= 0 else len(patch)]
    return '\n'.join(line[1:] for line in section.splitlines()
                     if line.startswith('+') and not line.startswith('+++'))


def is_declared(source: str, name: str) -> bool:
    return bool(re.search(r'\b' + re.escape(name) + r'\s*\(', source))


def audit(platform_h: str, nvn_vk: str, modules_cmake: str, smw_patch: str) -> dict:
    ps4_platform = extracted_additions(smw_patch, 'runtime/src/platform_ps4.cpp')
    ps4_wsi = extracted_additions(smw_patch, 'runtime/src/ps4/ps4_vk_wsi.cpp')
    checks = []

    def check(code: str, description: str, condition: bool):
        checks.append({'code': code, 'description': description, 'present_in_sources': bool(condition)})

    for name in CALLBACKS:
        check('contract.' + name,
              f'Contrato Castlevania + chamada NVN + implementação PS4 referencial: {name}',
              is_declared(platform_h, name) and
              is_declared(nvn_vk, name) and is_declared(ps4_platform, name))

    for name in EXTRA_PLATFORM:
        check('platform.' + name,
              f'Assinatura presente na interface e implementação referencial PS4: {name}',
              is_declared(platform_h, name) and is_declared(ps4_platform, name))

    check('wsi.file', 'SMW adiciona backend Vulkan para VideoOut no PS4',
          bool(ps4_wsi) and 'namespace nx::plat::ps4' in ps4_wsi)
    check('wsi.headless', 'Referência oferece extensão VK_EXT_headless_surface',
          'VK_EXT_HEADLESS_SURFACE_EXTENSION_NAME' in ps4_platform and
          'vkCreateHeadlessSurfaceEXT' in ps4_platform)
    check('wsi.swapchain', 'Implementação referencial intercepta swapchain/present',
          'CreateSwapchainKHR' in ps4_wsi and 'QueuePresentKHR' in ps4_wsi)
    check('wsi.videoout', 'Implementação referencial conversa com saída VideoOut',
          'sceVideoOutRegisterBuffers' in ps4_wsi and 'sceVideoOutSubmitFlip' in ps4_wsi)
    check('wsi.radv_flip', 'Implementação referencial depende de Mesa/RADV PS4',
          'ac_ps4_submit_flip' in ps4_wsi)
    check('castlevania.subsdk0', 'Perfil Castlevania inclui módulo adicional subsdk0',
          bool(re.search(r'\bsubsdk0\b', modules_cmake)))

    critical = {'contract.' + name for name in CALLBACKS} | {
        'wsi.file', 'wsi.headless', 'wsi.swapchain', 'wsi.videoout', 'wsi.radv_flip',
        'castlevania.subsdk0'
    }
    missing = [item['code'] for item in checks
               if item['code'] in critical and not item['present_in_sources']]
    return {
        'scope': 'AUDITORIA DE CODIGO, NAO TESTE NO PS4',
        'critical_source_matches': not missing,
        'critical_missing': missing,
        'checks': checks,
        'next_actions': [
            'Portar os serviços de janela/superficie de nx::plat preservando o contrato do runtime.',
            'Integrar e compilar um backend Vulkan PS4 real com Mesa/RADV e VideoOut.',
            'Adequar os três módulos de Castlevania: main, sdk e subsdk0.',
            'Só então gerar PKG de diagnóstico GPU e validar em hardware.',
        ],
        'not_proven': [
            'Vulkan ou NVN funcionando no PS4 deste projeto',
            'Código recompilado de Castlevania gerado ou ligado',
            'Shader ou quadro do jogo apresentado',
            'Jogo jogável ou desempenho',
        ],
    }


def markdown_report(result: dict) -> str:
    lines = [
        '# Castlevania PS4 v1.2 — auditoria da ponte gráfica',
        '',
        '**Escopo:** análise estática de código público; NÃO valida execução no PS4.',
        '',
        '| Contrato ou dependência | Encontrado nas fontes? |',
        '| --- | :---: |',
    ]
    for item in result['checks']:
        lines.append(f"| `{item['code']}` — {item['description']} | " +
                     ('✅' if item['present_in_sources'] else '❌') + ' |')
    lines += ['', '## Resultado da análise', '']
    if result['critical_source_matches']:
        lines.append('Contratos mínimos identificados nos códigos de referência. Isso NÃO significa integração concluída.')
    else:
        lines.append('Faltam contratos importantes nas fontes consultadas: ' + ', '.join(result['critical_missing']))
    lines += ['', '## O que falta implementar', '']
    for action in result['next_actions']:
        lines.append('- ' + action)
    lines += ['', '## O que o resultado NÃO comprova', '']
    for caveat in result['not_proven']:
        lines.append('- ' + caveat)
    lines.append('')
    return '\n'.join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--castlevania', type=Path, required=True, help='checkout do projeto publico SwonDev')
    p.add_argument('--smw', type=Path, required=True, help='checkout do projeto publico iHaiDeeZ/SMW')
    p.add_argument('--out-dir', type=Path, required=True)
    args = p.parse_args()
    c, s = args.castlevania, args.smw
    result = audit(
        (c / 'runtime/src/platform.h').read_text(encoding='utf-8'),
        (c / 'runtime/src/nvn/nvn_vk.cpp').read_text(encoding='utf-8'),
        (c / 'games/castlevania/modules.cmake').read_text(encoding='utf-8'),
        (s / 'patches/wonder-ps4.patch').read_text(encoding='utf-8'),
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / 'graficos-auditoria.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (args.out_dir / 'graficos-auditoria.md').write_text(markdown_report(result), encoding='utf-8')
    print(markdown_report(result))
    return 0 if result['critical_source_matches'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
