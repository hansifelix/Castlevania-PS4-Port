#!/usr/bin/env python3
"""Deriva workflow 73 do 72, conservando ambiente pinned e testes sem dados comerciais."""
from pathlib import Path
SOURCE=Path('.github/workflows/kazuma-etapa72-threads-nativas.yml')
DEST=Path('.github/workflows/kazuma-etapa73-input-vulkan.yml')
def generate(s):
 a="name: 'Kazuma Etapa 72 - scePthread nativo PS4 (SEM JOGO / SEM PKG)'"
 b="name: 'Kazuma Etapa 73 - contrato input Vulkan PS4 (SEM JOGO / SEM PKG)'"
 if s.count(a)!=1:raise ValueError('workflow72 inesperado')
 s=s.replace(a,b,1)
 marker="      - 'tools/etapa72/**'"
 if s.count(marker)!=1:raise ValueError('gatilho 72 mudou')
 s=s.replace(marker,marker+"\n      - 'tools/etapa73/**'\n      - 'docs/KAZUMA_ETAPA73.md'\n      - 'tools/etapa62/**'",1)
 step="""      - name: Integrar 5 APIs threads PS4 com scePthread e tentar link ESTRITO
        run: |
          set -euo pipefail
          bash tools/etapa72/integrar_threads_nativas.sh
"""
 new=step+"""      - name: Testar mapeamento DS4 para contrato Npad (Linux, NAO PS4)
        run: |
          set -euo pipefail
          python3 -m unittest discover -s tools/etapa73 -p 'test_*.py' -v
          clang++-18 -std=c++20 -O0 -Wall -Wextra -Werror \\
            -I"$KAZUMA_NX_SOURCE/runtime/src" -Itools/etapa73 \\
            tools/etapa73/test_pad.cpp -o "$RUNNER_TEMP/kazuma73_pad_test"
          "$RUNNER_TEMP/kazuma73_pad_test"
      - name: Integrar read_pad + tres APIs Vulkan reais ao nx boot (SEM JOGO)
        run: |
          set -euo pipefail
          bash tools/etapa73/integrar.ps4.sh
"""
 if s.count(step)!=1:raise ValueError('bloco 72 nao encontrado')
 s=s.replace(step,new,1)
 old='name: kazuma-etapa72-sce-pthread-sem-jogo'
 if s.count(old)!=1:raise ValueError('artefato72 nao encontrado')
 s=s.replace(old,'name: kazuma-etapa73-input-vulkan-sem-jogo',1)
 return s
if __name__=='__main__':
 if not SOURCE.exists():raise SystemExit('Workflow 72 ausente; execute no repositorio atualizado')
 DEST.write_text(generate(SOURCE.read_text()))
 print('KAZUMA73: workflow pronto',DEST)
