#!/usr/bin/env python3
"""Deriva Etapa 42 da Etapa 41 validada no CI, sem copiar componentes comerciais."""
from pathlib import Path

origem = Path('.github/workflows/kazuma-etapa41-integracao-runtime.yml')
destino = Path('.github/workflows/kazuma-etapa42-link-executavel.yml')


def substituir_unico(texto: str, anterior: str, proximo: str) -> str:
    n = texto.count(anterior)
    if n != 1:
        raise RuntimeError(f'Esperada exatamente 1 ocorrencia (houve {n}): {anterior[:85]}')
    return texto.replace(anterior, proximo, 1)


def gerar() -> Path:
    if not origem.is_file():
        raise RuntimeError('Etapa 41 nao esta na main (workflow ausente).')
    if not Path('tools/etapa41/integrar_runtime.sh').is_file():
        raise RuntimeError('Etapa 41 nao foi integrada a main: falta integrador.')
    if not Path('tools/etapa10/testar_link_homebrew.sh').is_file():
        raise RuntimeError('Falta teste de controle da Etapa 10.')
    texto = origem.read_text(encoding='utf-8')
    texto = substituir_unico(
        texto,
        "name: 'Kazuma Etapa 41 - integrar 87 objetos e 8 APIs PS4 (SEM PKG)'",
        "name: 'Kazuma Etapa 42 - diagnostico de link ELF PS4 (SEM PKG)'",
    )
    texto = substituir_unico(
        texto,
        "      - '.github/workflows/kazuma-etapa41-integracao-runtime.yml'\n"
        "      - 'tools/etapa41/**'\n"
        "      - 'tools/etapa40/**'",
        "      - '.github/workflows/kazuma-etapa42-link-executavel.yml'\n"
        "      - 'tools/etapa42/**'",
    )
    insercao = (
        "      - name: Testar analisador do linker\n"
        "        run: |\n"
        "          set -euo pipefail\n"
        "          python3 -m unittest discover -s tools/etapa42 -p 'test_*.py' -v\n"
        "      - name: Tentar link executavel ESTRITO e explicar bloqueios\n"
        "        run: |\n"
        "          set -euo pipefail\n"
        "          bash tools/etapa42/tentar_link_real.sh\n\n"
    )
    texto = substituir_unico(
        texto,
        '      - name: Publicar diagnosticos SEM artefatos comerciais ou PKG\n',
        insercao + '      - name: Publicar diagnosticos SEM artefatos comerciais ou PKG\n',
    )
    texto = substituir_unico(
        texto,
        'name: kazuma-etapa41-integracao-87-objetos-8-apis-sem-pkg',
        'name: kazuma-etapa42-link-estrito-e-dependencias-sem-pkg',
    )
    destino.write_text(texto, encoding='utf-8')
    return destino


if __name__ == '__main__':
    print('Workflow gerado:', gerar())
