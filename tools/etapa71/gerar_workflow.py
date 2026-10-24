#!/usr/bin/env python3
"""Reaproveita o workflow da Etapa 50 sem mentir sobre o artefato gerado."""
from pathlib import Path
import sys

SOURCE=Path('.github/workflows/kazuma-etapa50-memoria-runtime.yml')
DEST=Path('.github/workflows/kazuma-etapa71-runtime-threads.yml')

def generate(source):
    s=source
    old="name: 'Kazuma Etapa 50 - memoria virtual do runtime PS4 (SEM JOGO / SEM PKG)'"
    if s.count(old)!=1: raise ValueError('Workflow base mudou: revisar manualmente')
    s=s.replace(old,"name: 'Kazuma Etapa 71 - threads reais do runtime PS4 (SEM JOGO / SEM PKG)'",1)
    old="      - 'tools/etapa50/**'"
    if s.count(old)!=1: raise ValueError('Gatilho inesperado')
    s=s.replace(old,old+"\n      - 'tools/etapa71/**'\n      - 'docs/KAZUMA_ETAPA71.md'",1)
    old='      - name: Publicar diagnosticos SEM artefatos comerciais ou PKG'
    if s.count(old)!=1: raise ValueError('Passo de artefatos nao encontrado')
    insert='''      - name: Testar threads POSIX em Linux (NAO PS4)
        run: |
          set -euo pipefail
          python3 -m unittest discover -s tools/etapa71 -p 'test_*.py' -v
          clang++-18 -std=c++20 -O1 -Wall -Wextra -Werror -pthread \\
            tools/etapa71/platform_ps4_threads.cpp tools/etapa71/test_threads.cpp \\
            -o "$RUNNER_TEMP/kazuma71_thread_test"
          "$RUNNER_TEMP/kazuma71_thread_test"
      - name: Integrar 3 APIs reais de threads ao nx boot PS4 e tentar link ESTRITO
        run: |
          set -euo pipefail
          bash tools/etapa71/integrar_threads.sh
'''
    s=s.replace(old,insert+old,1)
    old='name: kazuma-etapa50-memoria-ps4-analise-sem-pkg'
    if s.count(old)!=1:raise ValueError('Nome artefato base mudou')
    s=s.replace(old,'name: kazuma-etapa71-threads-boot-sem-jogo',1)
    return s
if __name__=='__main__':
    if not SOURCE.is_file():sys.exit('Falta etapa50 no repo, não continuar')
    DEST.write_text(generate(SOURCE.read_text()))
    print('KAZUMA71: workflow gerado:',DEST)
