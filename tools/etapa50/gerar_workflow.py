#!/usr/bin/env python3
"""Derivar CI50 a partir da CI49 consolidada; nao editar checkpoints antigos."""
from pathlib import Path
SRC=Path('.github/workflows/kazuma-etapa49-host-basics.yml')
DST=Path('.github/workflows/kazuma-etapa50-memoria-runtime.yml')

def once(s,a,b):
    n=s.count(a)
    if n!=1: raise RuntimeError(f'Esperado 1 ancora, encontrado {n}: {a!r}')
    return s.replace(a,b,1)

def derive(s):
    s=once(s,"name: 'Kazuma Etapa 49 - ligar 6 APIs host ao boot runtime PS4 (SEM JOGO / SEM PKG)'",
        "name: 'Kazuma Etapa 50 - memoria virtual do runtime PS4 (SEM JOGO / SEM PKG)'")
    s=once(s,"      - '.github/workflows/kazuma-etapa49-host-basics.yml'",
        "      - '.github/workflows/kazuma-etapa50-memoria-runtime.yml'\n      - 'tools/etapa50/**'\n      - 'docs/KAZUMA_ETAPA50.md'")
    step="""      - name: Testar memoria POSIX no Linux (NAO comprova PS4)
        run: |
          set -euo pipefail
          python3 -m unittest discover -s tools/etapa50 -p 'test_*.py' -v
          clang++-18 -std=c++20 -O1 -Wall -Wextra -Werror -pthread \\
            tools/etapa50/platform_ps4_memory.cpp \\
            tools/etapa50/test_memory_linux.cpp \\
            -o "$RUNNER_TEMP/kazuma50_memory_test"
          "$RUNNER_TEMP/kazuma50_memory_test"
      - name: Integrar tres APIs PS4 de memoria e medir delta de simbolos
        run: |
          set -euo pipefail
          bash tools/etapa50/integrar_memoria.sh

"""
    s=once(s,'      - name: Publicar diagnosticos SEM artefatos comerciais ou PKG\n',step+'      - name: Publicar diagnosticos SEM artefatos comerciais ou PKG\n')
    s=once(s,'name: kazuma-etapa49-delta-dependencias-boot-real-sem-pkg',
        'name: kazuma-etapa50-memoria-ps4-analise-sem-pkg')
    return s

if __name__=='__main__':
    if not SRC.is_file():raise SystemExit('Falta PR45 integrada ao main, nao publicar')
    if not Path('tools/etapa49/integrar_host_basics.sh').is_file():raise SystemExit('Falta codigo etapa49 na main')
    DST.write_text(derive(SRC.read_text(encoding='utf8')),encoding='utf8')
    print('Gerado workflow:',DST)
