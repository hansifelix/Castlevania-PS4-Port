#!/usr/bin/env python3
"""Extends the existing Etapa73 GitHub Actions setup, fails if anchors change."""
from pathlib import Path
SOURCE=Path('.github/workflows/kazuma-etapa73-input-vulkan.yml')
DEST=Path('.github/workflows/kazuma-etapa74-videoout-runtime.yml')

def generate(s):
    title="name: 'Kazuma Etapa 73 - contrato input Vulkan PS4 (SEM JOGO / SEM PKG)'"
    assert s.count(title)==1, 'Workflow73 title changed'
    s=s.replace(title,"name: 'Kazuma Etapa 74 - display VideoOut nx runtime PS4 (SEM JOGO / SEM PKG)'",1)
    marker="      - 'tools/etapa73/**'"
    assert s.count(marker)==1, 'Workflow73 trigger changed'
    s=s.replace(marker,marker+"\n      - 'tools/etapa74/**'\n      - 'docs/KAZUMA_ETAPA74.md'",1)
    anchor='''      - name: Integrar read_pad + tres APIs Vulkan reais ao nx boot (SEM JOGO)
        run: |
          set -euo pipefail
          bash tools/etapa73/integrar.ps4.sh
'''
    assert s.count(anchor)==1, 'Workflow73 integration step changed'
    after='''      - name: Testar contrato VideoOut no Linux (MOCK declarado, NAO PS4)
        run: |
          set -euo pipefail
          python3 -m unittest discover -s tools/etapa74 -p 'test_*.py' -v
          clang++-18 -std=c++20 -O1 -Wall -Wextra -Werror \\
            -Itools/etapa74/mock \\
            tools/etapa74/platform_ps4_display.cpp tools/etapa74/test_display_host.cpp \\
            -o "$RUNNER_TEMP/kazuma74_videoout_host"
          "$RUNNER_TEMP/kazuma74_videoout_host"
      - name: Integrar seis APIs reais VideoOut ao boot (SEM JOGO)
        run: |
          set -euo pipefail
          bash tools/etapa74/integrar_videoout.sh
'''
    s=s.replace(anchor,anchor+after,1)
    old='name: kazuma-etapa73-input-vulkan-sem-jogo'
    assert s.count(old)==1, 'Artifact 73 name changed'
    s=s.replace(old,'name: kazuma-etapa74-videoout-sem-jogo',1)
    return s

if __name__=='__main__':
    assert SOURCE.is_file(), 'Need baseline workflow73 merged in main'
    DEST.write_text(generate(SOURCE.read_text()))
    print('KAZUMA74 workflow created:',DEST)
