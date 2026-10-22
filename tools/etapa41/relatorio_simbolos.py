#!/usr/bin/env python3
"""Relatorio objetivo de simbolos do runtime PS4. Nao usa arquivos do jogo."""
from pathlib import Path
import sys


def linhas(caminho: Path) -> list[str]:
    return caminho.read_text(encoding="utf-8").splitlines()


def nomes_nao_definidos(texto: list[str]) -> set[str]:
    # llvm-nm -C -u imprime "                 U namespace::simbolo(...)"
    return {l.strip().removeprefix("U ").strip() for l in texto if l.strip()}


def gerar(pasta: Path) -> str:
    antes = nomes_nao_definidos(linhas(pasta / "INDEFINIDOS_ANTES.txt"))
    depois = nomes_nao_definidos(linhas(pasta / "INDEFINIDOS_DEPOIS.txt"))
    novos = linhas(pasta / "DEFINIDOS_CINCO_APIS.txt")
    esperados = ["fopen_utf8(", "ftell64(", "fseek64(", "read_at(", "make_dirs("]

    for nome in esperados:
        prefixo = "nx::plat::" + nome
        if not any(prefixo in linha for linha in novos):
            raise RuntimeError(f"API x86-64 NAO encontrada no objeto: {prefixo}")
        if any(prefixo in simb for simb in depois):
            raise RuntimeError(f"API ainda indefinida apos link: {prefixo}")

    resolvidos = sorted(antes - depois)
    introduzidos = sorted(depois - antes)
    plat_antes = {s for s in antes if "nx::plat::" in s}
    plat_depois = {s for s in depois if "nx::plat::" in s}
    usados_das_cinco = [
        n for n in esperados if any("nx::plat::" + n in x for x in plat_antes)
    ]

    (pasta / "SIMBOLOS_RESOLVIDOS.txt").write_text("\n".join(resolvidos) + "\n", encoding="utf-8")
    (pasta / "SIMBOLOS_INTRODUZIDOS.txt").write_text("\n".join(introduzidos) + "\n", encoding="utf-8")
    (pasta / "PLATAFORMA_AINDA_PENDENTE.txt").write_text("\n".join(sorted(plat_depois)) + "\n", encoding="utf-8")
    (pasta / "SIMBOLOS_AINDA_PENDENTES.txt").write_text("\n".join(sorted(depois)) + "\n", encoding="utf-8")

    grupo = {
        "PLATAFORMA_NX": [s for s in depois if "nx::plat::" in s],
        "OUTRAS_NX": [s for s in depois if "nx::" in s and "nx::plat::" not in s],
        "CXX_ABI": [s for s in depois if s.startswith(("std::", "__cxa", "_Unwind", "operator new", "operator delete"))],
        "VULKAN": [s for s in depois if s.startswith("vk") or "vulkan" in s.lower()],
        "SDL": [s for s in depois if s.startswith("SDL_")],
    }
    grupos_vistos = set().union(*(set(v) for v in grupo.values()))
    grupo["OUTRAS_DEPENDENCIAS"] = sorted(depois - grupos_vistos)
    for nome, valores in grupo.items():
        (pasta / f"PENDENTES_{nome}.txt").write_text("\n".join(sorted(valores)) + "\n", encoding="utf-8")

    status = [
        "STATUS=LINK_RELOCAVEL_PARCIAL_SUCESSO",
        "OBJETOS_RUNTIME=87 (confirmados pelo teste da Etapa 39)",
        "OBJETOS_PS4_ADICIONADOS=2 (adaptador core + adaptador de arquivos)",
        "APIS_DEFINIDAS_NO_OBJETO_CORE=3",
        "APIS_DEFINIDAS_NO_OBJETO_ARQUIVOS=5",
        f"APIS_ARQUIVOS_USADAS_PELO_RUNTIME={len(usados_das_cinco)}",
        "APIS_ARQUIVOS_USADAS_NOMES=" + (",".join(usados_das_cinco) or "nenhuma"),
        f"SIMBOLOS_INDEFINIDOS_ANTES={len(antes)}",
        f"SIMBOLOS_INDEFINIDOS_DEPOIS={len(depois)}",
        f"SIMBOLOS_RESOLVIDOS_TOTAL={len(resolvidos)}",
        f"SIMBOLOS_NOVOS_TOTAL={len(introduzidos)}",
        f"NX_PLATAFORMA_PENDENTES_ANTES={len(plat_antes)}",
        f"NX_PLATAFORMA_PENDENTES_DEPOIS={len(plat_depois)}",
        *[f"PENDENTES_{nome}={len(valores)}" for nome, valores in grupo.items()],
        "AVISO=Link -r permite dependencias indefinidas; NAO gera executavel, PKG ou teste no PS4.",
        "PROXIMO_PASSO=Resolver pendencias reais para tentar um ELF executavel minimal na Etapa 42.",
    ]
    saida = "\n".join(status) + "\n"
    (pasta / "RESULTADO_ETAPA41.txt").write_text(saida, encoding="utf-8")
    return saida


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: relatorio_simbolos.py DIRETORIO_RELATORIOS")
    print(gerar(Path(sys.argv[1])))
