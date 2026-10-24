#!/usr/bin/env python3
"""Gera workflow 75 a partir do workflow 74 merged; não duplica etapas."""
from pathlib import Path
SOURCE=Path('.github/workflows/kazuma-etapa74-videoout-runtime.yml')
DEST=Path('.github/workflows/kazuma-etapa75-audio-runtime.yml')

def generate(s):
    old="name: 'Kazuma Etapa 74 - display VideoOut nx runtime PS4 (SEM JOGO / SEM PKG)'"
    new="name: 'Kazuma Etapa 75 - AudioOut nx runtime PS4 (SEM JOGO / SEM PKG)'"
    assert s.count(old)==1,'Workflow 74 desconhecido: título mudou'
    s=s.replace(old,new,1)
    marker="      - 'tools/etapa74/**'"
    assert s.count(marker)==1,'Workflow 74 desconhecido: paths mudaram'
    s=s.replace(marker,marker+"\n      - 'tools/etapa75/**'\n      - 'docs/KAZUMA_ETAPA75.md'",1)
    anchor="""      - name: Integrar seis APIs reais VideoOut ao boot (SEM JOGO)
        run: |
          set -euo pipefail
          bash tools/etapa74/integrar_videoout.sh
"""
    assert s.count(anchor)==1,'Não encontrei bloco 74 original'
    extra="""      - name: Testes de AudioOut 48kHz (host Linux com mock, NAO PS4)
        run: |
          set -euo pipefail
          python3 -m unittest discover -s tools/etapa75 -p 'test_*.py' -v
          clang++-18 -std=c++20 -O1 -Wall -Wextra -Werror \\
            -Itools/etapa75/mock \\
            tools/etapa75/platform_ps4_audio.cpp tools/etapa75/test_audio_host.cpp \\
            -o "$RUNNER_TEMP/kazuma75_audio_host"
          "$RUNNER_TEMP/kazuma75_audio_host"
      - name: Integrar as 3 APIs nx audio via SceAudioOut (SEM JOGO)
        run: |
          set -euo pipefail
          bash tools/etapa75/integrar_audio.sh
"""
    s=s.replace(anchor,anchor+extra,1)
    art='name: kazuma-etapa74-videoout-sem-jogo'
    assert s.count(art)==1,'Workflow 74 desconhecido: artefato'
    s=s.replace(art,'name: kazuma-etapa75-audioout-sem-jogo',1)
    return s

if __name__=='__main__':
    if not SOURCE.is_file(): raise SystemExit('Workflow 74 ausente; faça merge da PR 62 primeiro')
    DEST.write_text(generate(SOURCE.read_text()))
    print('KAZUMA75 workflow pronto:',DEST)
