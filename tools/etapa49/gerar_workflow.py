#!/usr/bin/env python3
"""Derivar workflow49 do workflow48 auditado sem editar etapas anteriores."""
from pathlib import Path
src=Path('.github/workflows/kazuma-etapa48-boot-runtime.yml')
dst=Path('.github/workflows/kazuma-etapa49-host-basics.yml')

def replace_one(txt,old,new):
    assert txt.count(old)==1, f'Workflow upstream mudou, esperado 1: {old!r}, presente {txt.count(old)}'
    return txt.replace(old,new,1)

def derive(text):
    text=replace_one(text,
        "name: 'Kazuma Etapa 48 - tentar boot real do runtime PS4 (SEM JOGO / SEM PKG)'",
        "name: 'Kazuma Etapa 49 - ligar 6 APIs host ao boot runtime PS4 (SEM JOGO / SEM PKG)'")
    text=replace_one(text,
        "      - '.github/workflows/kazuma-etapa48-boot-runtime.yml'",
        "      - '.github/workflows/kazuma-etapa49-host-basics.yml'\n      - 'tools/etapa49/**'\n      - 'docs/KAZUMA_ETAPA49.md'")
    step='''      - name: Testar auditoria e funcoes portaveis no Linux (NAO PS4)
        run: |
          set -euo pipefail
          python3 -m unittest discover -s tools/etapa49 -p 'test_*.py' -v
          clang++-18 -std=c++20 -O0 -Wall -Wextra -Werror \
            tools/etapa49/platform_ps4_host_basics.cpp \
            tools/etapa49/test_host.cpp -o "$RUNNER_TEMP/kazuma49_host_test"
          "$RUNNER_TEMP/kazuma49_host_test"
      - name: Ligar APIs PS4 de host sem falsificar grafico, audio e memoria
        run: |
          set -euo pipefail
          bash tools/etapa49/integrar_host_basics.sh

'''
    text=replace_one(text,
        '      - name: Publicar diagnosticos SEM artefatos comerciais ou PKG\n',
        step+'      - name: Publicar diagnosticos SEM artefatos comerciais ou PKG\n')
    text=replace_one(text,
        'name: kazuma-etapa48-boot-real-e-bloqueios-sem-pkg',
        'name: kazuma-etapa49-delta-dependencias-boot-real-sem-pkg')
    return text

if __name__=='__main__':
    assert src.is_file(), 'Integre a PR #44 antes de publicar a 49'
    assert Path('tools/etapa48/tentar_boot_real.sh').is_file(), 'Falta etapa48'
    dst.write_text(derive(src.read_text(encoding='utf-8')),encoding='utf-8')
    print('Workflow criado:',dst)
