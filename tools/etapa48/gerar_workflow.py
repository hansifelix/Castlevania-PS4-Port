#!/usr/bin/env python3
"""Deriva Etapa 48 de workflow Etapa 42 ja validado, sem reescrever o pipeline."""
from pathlib import Path

SRC=Path('.github/workflows/kazuma-etapa42-link-executavel.yml')
DST=Path('.github/workflows/kazuma-etapa48-boot-runtime.yml')

def derive(s: str) -> str:
    old="name: 'Kazuma Etapa 42 - diagnostico de link ELF PS4 (SEM PKG)'"
    assert s.count(old)==1, 'Workflow 42 alterado: abortando'
    s=s.replace(old,"name: 'Kazuma Etapa 48 - tentar boot real do runtime PS4 (SEM JOGO / SEM PKG)'")
    old="      - '.github/workflows/kazuma-etapa42-link-executavel.yml'"
    assert s.count(old)==1
    s=s.replace(old,"      - '.github/workflows/kazuma-etapa48-boot-runtime.yml'\n      - 'tools/etapa48/**'\n      - 'docs/KAZUMA_ETAPA48.md'")
    # Usar a implementacao de clock testada na Etapa 47 em vez do prototipo 38.
    assert s.count('tools/etapa38/platform_ps4_core.cpp')==2
    s=s.replace('tools/etapa38/platform_ps4_core.cpp','tools/etapa47/platform_ps4_core_clock.cpp')
    old='      - name: Publicar diagnosticos SEM artefatos comerciais ou PKG\n'
    assert s.count(old)==1
    step='''      - name: Testar analisador da Etapa 48
        run: |
          set -euo pipefail
          python3 -m unittest discover -s tools/etapa48 -p 'test_*.py' -v
      - name: Compilar nx boot real e diagnosticar simbolos restantes
        run: |
          set -euo pipefail
          bash tools/etapa48/tentar_boot_real.sh
          test -s relatorios/etapa48/LEIA_PRIMEIRO.txt
          test -s relatorios/etapa48/RESUMO.json

'''
    s=s.replace(old,step+old)
    old='name: kazuma-etapa42-link-estrito-e-dependencias-sem-pkg'
    assert s.count(old)==1
    s=s.replace(old,'name: kazuma-etapa48-boot-real-e-bloqueios-sem-pkg')
    return s

def main():
    assert SRC.is_file(), 'Etapa42 nao encontrada na branch main'
    assert Path('tools/etapa47/platform_ps4_core_clock.cpp').is_file(), 'Integre Etapa47 primeiro'
    DST.write_text(derive(SRC.read_text(encoding='utf-8')), encoding='utf-8')
    print('Workflow criado:',DST)
if __name__=='__main__':
    main()
