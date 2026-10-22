#!/usr/bin/env python3
"""KAZUMA Test 09: teste minimo do Submit Done exigido no suspend do PS4.

Roda DEPOIS do patch Test08, na copia TEMPORARIA do exemplo MIT do kit.
Sem garantias de compatibilidade entre GNM e a camada Vulkan RADV.
"""
from pathlib import Path
import sys

MARK = 'KAZUMA_TEST09_GNM_SUBMITDONE'
INCLUDE = '#include <orbis/libkernel.h>\n'
ORIGINAL = '''    if (pause_result == VK_SUCCESS)
        say("triangle: KAZUMA_TEST08 GPU idle reached; no more frame submits");
    else
        say("triangle: KAZUMA_TEST08 GPU idle failed; do NOT assume suspend is safe");'''
REPLACEMENT = '''    if (pause_result == VK_SUCCESS) {
        say("triangle: KAZUMA_TEST08 GPU idle reached; no more frame submits");
        /* KAZUMA_TEST09_GNM_SUBMITDONE: PS4 trata vkDeviceWaitIdle e o
         * sceGnmSubmitDone como operacoes diferentes. Testar SOMENTE apos
         * Vulkan confirmar GPU ociosa. Nao prova ausencia de CE-34878-0. */
        int32_t gnm_result = sceGnmSubmitDone();
        say("triangle: KAZUMA_TEST09 sceGnmSubmitDone -> %ld (0x%08lx)",
            (long)gnm_result, (unsigned long)(uint32_t)gnm_result);
    } else {
        say("triangle: KAZUMA_TEST08 GPU idle failed; do NOT assume suspend is safe");
        say("triangle: KAZUMA_TEST09 skipping GNM call (Vulkan not idle)");
    }'''

def patch(source: str) -> str:
    if MARK in source:
        raise ValueError('Test09 ja inserido')
    if source.count(INCLUDE) != 1 or source.count(ORIGINAL) != 1:
        raise ValueError('Fonte nao corresponde ao Test08 esperado; abortando sem modificar')
    if 'KAZUMA_TEST08_MAX_FRAMES = 300UL' not in source:
        raise ValueError('Falta codigo Test08')
    return (source.replace(INCLUDE, INCLUDE + '#include <orbis/GnmDriver.h>\n', 1)
                  .replace(ORIGINAL, REPLACEMENT, 1))

def main() -> None:
    if len(sys.argv) != 2:
        sys.exit('Uso: python3 patch_triangle_gnm_submitdone.py /caminho/triangle.c')
    file = Path(sys.argv[1])
    if not file.is_file():
        sys.exit('ERRO: fonte nao encontrado')
    try:
        modified = patch(file.read_text(encoding='utf-8'))
    except ValueError as exc:
        sys.exit('ERRO: ' + str(exc))
    file.write_text(modified, encoding='utf-8')
    print('OK: Test09 inclui sceGnmSubmitDone apos vkDeviceWaitIdle==VK_SUCCESS.')
    print('AVISO: compilacao, execucao e correcao de suspensao ainda nao comprovadas.')

if __name__ == '__main__':
    main()
