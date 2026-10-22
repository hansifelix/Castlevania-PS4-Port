#!/usr/bin/env python3
"""Etapa 28: patch minimo do exemplo MIT triangle.c do orbis-porting-kit.

Pausa submissions apos numero finito de frames e chama vkDeviceWaitIdle.
Nao alega que CE-34878-0 esteja corrigido; requer nova validacao em hardware.
"""
from pathlib import Path
import sys

MARK = 'KAZUMA_TEST08_MAX_FRAMES'
OLD_LOOP = '''    say("triangle: setup complete - presenting");
    unsigned long frame = 0;
    for (;;) {'''
NEW_LOOP = '''    say("triangle: setup complete - presenting; KAZUMA_TEST08 300 frames then pause");
    unsigned long frame = 0;
    /* KAZUMA_TEST08_MAX_FRAMES: limitar submissions antes de fechar via menu PS.
     * Hipotese a testar: submitDone timeout durante suspend com loop de apresentacao ativo.
     * Isso nao prova seguranca do suspend e nao e um port de jogo. */
    const unsigned long KAZUMA_TEST08_MAX_FRAMES = 300UL;
    for (; frame < KAZUMA_TEST08_MAX_FRAMES;) {'''
OLD_TAIL = '''    say("triangle: stopped after %lu frame(s) - idling; close from the PS button menu", frame);
    for (;;)
        sleep(1);
}'''
NEW_TAIL = '''    say("triangle: KAZUMA_TEST08 stopping GPU submissions after %lu frame(s)", frame);
    VkResult pause_result = vkDeviceWaitIdle(device);
    say("triangle: KAZUMA_TEST08 vkDeviceWaitIdle -> %d", (int)pause_result);
    if (pause_result == VK_SUCCESS)
        say("triangle: KAZUMA_TEST08 GPU idle reached; no more frame submits");
    else
        say("triangle: KAZUMA_TEST08 GPU idle failed; do NOT assume suspend is safe");
    /* Nao retornar main: SDK upstream documenta SIGSYS/CE-34878-0 ao retornar.
     * Nao destruir objetos aqui: variamos apenas uma causa possivel por teste. */
    say("triangle: KAZUMA_TEST08 wait for PS menu close (experimental)");
    for (;;)
        sleep(1);
}'''

def patch(s: str) -> str:
    if MARK in s:
        raise ValueError('Marcador KAZUMA_TEST08 ja existe; nada modificado')
    if s.count(OLD_LOOP) != 1 or s.count(OLD_TAIL) != 1:
        raise ValueError('Fonte upstream divergiu das ancoras esperadas; abortar')
    return s.replace(OLD_LOOP, NEW_LOOP, 1).replace(OLD_TAIL, NEW_TAIL, 1)

def main():
    if len(sys.argv) != 2:
        sys.exit('Uso: python3 patch_triangle_pause.py /caminho/triangle.c')
    p = Path(sys.argv[1])
    if not p.is_file():
        sys.exit('ERRO: fonte triangle.c nao encontrado')
    s = p.read_text(encoding='utf-8')
    try:
        out = patch(s)
    except ValueError as exc:
        sys.exit('ERRO: ' + str(exc))
    p.write_text(out, encoding='utf-8')
    print('OK: loop Vulkan agora termina apos 300 frames e tenta vkDeviceWaitIdle.')
    print('Isto nao confirma corrigir CE-34878-0: so teste futuro no console.')

if __name__ == '__main__':
    main()
