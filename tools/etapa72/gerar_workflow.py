#!/usr/bin/env python3
"""Gera workflow 72 reproduzível a partir do 71 existente no repositório."""
from pathlib import Path
SOURCE=Path('.github/workflows/kazuma-etapa71-runtime-threads.yml')
DEST=Path('.github/workflows/kazuma-etapa72-threads-nativas.yml')

def generate(text):
    src="name: 'Kazuma Etapa 71 - threads reais do runtime PS4 (SEM JOGO / SEM PKG)'"
    dst="name: 'Kazuma Etapa 72 - scePthread nativo PS4 (SEM JOGO / SEM PKG)'"
    assert text.count(src)==1, 'Workflow base 71 mudou'
    text=text.replace(src,dst,1)
    old="      - 'tools/etapa71/**'"
    assert text.count(old)==1, 'Gatilhos 71 mudaram'
    text=text.replace(old,old+"\n      - 'tools/etapa72/**'\n      - 'docs/KAZUMA_ETAPA72.md'",1)
    step='''      - name: Integrar 3 APIs reais de threads ao nx boot PS4 e tentar link ESTRITO
        run: |
          set -euo pipefail
          bash tools/etapa71/integrar_threads.sh
'''
    new='''      - name: Testar contrato das 5 APIs no mock scePthread Linux (NAO PS4)
        run: |
          set -euo pipefail
          python3 -m unittest discover -s tools/etapa72 -p 'test_*.py' -v
          clang++-18 -std=c++20 -O1 -Wall -Wextra -Werror -pthread \\
            -D_GNU_SOURCE -DKAZUMA_MOCK_PS4 -Itools/etapa72/mock \\
            tools/etapa72/platform_ps4_threads_native.cpp tools/etapa72/test_native_threads.cpp \\
            -o "$RUNNER_TEMP/kazuma72_mock_test"
          "$RUNNER_TEMP/kazuma72_mock_test"
      - name: Integrar 5 APIs threads PS4 com scePthread e tentar link ESTRITO
        run: |
          set -euo pipefail
          bash tools/etapa72/integrar_threads_nativas.sh
'''
    assert text.count(step)==1, 'Não foi encontrado o bloco exato de integração 71'
    text=text.replace(step,new,1)
    old_art='name: kazuma-etapa71-threads-boot-sem-jogo'
    assert text.count(old_art)==1
    text=text.replace(old_art,'name: kazuma-etapa72-sce-pthread-sem-jogo',1)
    return text

if __name__=='__main__':
    if not SOURCE.exists(): raise SystemExit('Falta baseline .github/workflows Etapa71')
    DEST.write_text(generate(SOURCE.read_text()))
    print('KAZUMA72: workflow atualizado:',DEST)
