#!/usr/bin/env python3
"""Deriva etapa41 do workflow 39 testado, preservando passos e versoes fixadas."""
from pathlib import Path

ORIGEM = Path(".github/workflows/kazuma-etapa39-ligacao-runtime.yml")
DESTINO = Path(".github/workflows/kazuma-etapa41-integracao-runtime.yml")


def trocar_unico(texto: str, antigo: str, novo: str) -> str:
    ocorrencias = texto.count(antigo)
    if ocorrencias != 1:
        raise RuntimeError(f"Esperada 1 ocorrencia, houve {ocorrencias}: {antigo!r}")
    return texto.replace(antigo, novo, 1)


def criar() -> Path:
    if not ORIGEM.is_file():
        raise RuntimeError("Workflow Etapa 39 ausente; nao e seguro derivar Etapa 41.")
    if not Path("tools/etapa40/platform_ps4_files.cpp").is_file():
        raise RuntimeError("Etapa 40 ainda nao esta na branch main. Integre a PR #36 antes de executar.")
    src = ORIGEM.read_text(encoding="utf-8")
    src = trocar_unico(
        src,
        "name: 'Kazuma Etapa 39 - integrar 87 objetos com plataforma PS4 (SEM PKG)'",
        "name: 'Kazuma Etapa 41 - integrar 87 objetos e 8 APIs PS4 (SEM PKG)'",
    )
    src = trocar_unico(
        src,
        "      - '.github/workflows/kazuma-etapa39-ligacao-runtime.yml'",
        "      - '.github/workflows/kazuma-etapa41-integracao-runtime.yml'\n"
        "      - 'tools/etapa41/**'\n"
        "      - 'tools/etapa40/**'",
    )
    # Execucao independente na PR; nao altera o workflow 39 nem seu historico.
    bloco = """      - name: Integrar cinco APIs ao runtime e classificar pendencias
        run: |
          set -euo pipefail
          bash tools/etapa41/integrar_runtime.sh

"""
    src = trocar_unico(src,
        "      - name: Publicar diagnosticos SEM artefatos comerciais ou PKG\n",
        bloco + "      - name: Publicar diagnosticos SEM artefatos comerciais ou PKG\n",
    )
    src = trocar_unico(
        src,
        "name: kazuma-etapa39-ligacao-runtime-platform-ps4-sem-pkg",
        "name: kazuma-etapa41-integracao-87-objetos-8-apis-sem-pkg",
    )
    src = trocar_unico(src, "          path: relatorios/etapa39/\n", "          path: relatorios/\n")
    DESTINO.write_text(src, encoding="utf-8")
    return DESTINO


if __name__ == "__main__":
    print("Workflow gerado:", criar())
