#!/usr/bin/env python3
"""Classifica bloqueios do BOOT real, nunca interpreta check verde como jogo pronto."""
from __future__ import annotations
from pathlib import Path
import argparse
import json
import re


def extract_symbols(text: str) -> list[str]:
    """Nomes de 'llvm-nm -C -u' ou 'ld.lld error: undefined symbol'."""
    symbols: set[str] = set()
    for line in text.splitlines():
        m = re.search(r"(?:^|\s)U\s+(.+)$", line)
        if m:
            symbols.add(m.group(1).strip())
            continue
        m = re.search(r"undefined symbol:\s*(.+)$", line)
        if m:
            symbols.add(m.group(1).strip())
    return sorted(symbols)


def classification(name: str) -> str:
    if name in ("main", "nx_module_main", "nx_module_sdk") or \
       name.startswith("nx::game::") or "nx::linked_modules(" in name or "nx::ModuleInfo" in name:
        return "MODULOS_DO_JOGO_AUSENTES"
    if "nx::plat::" in name:
        return "PLATAFORMA_PS4_PENDENTE"
    if name.startswith(("vk", "SDL_")) or "vulkan" in name.lower():
        return "GRAFICOS_API"
    if name.startswith(("std::", "__cxa", "__gxx", "_Unwind", "operator new", "operator delete")):
        return "CXX_ABI"
    return "OUTRAS_DEPENDENCIAS"


def analyze(out: Path, compile_status: str, partial: str, strict: str) -> dict:
    log = (out / "LINK_ESTRITO_BOOT.log")
    nm = out / "SIMBOLOS_PENDENTES_BOOT.txt"
    read = lambda p: p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
    pending = extract_symbols(read(nm))
    linker = extract_symbols(read(log))
    groups = {k: [] for k in ("MODULOS_DO_JOGO_AUSENTES", "PLATAFORMA_PS4_PENDENTE", "GRAFICOS_API", "CXX_ABI", "OUTRAS_DEPENDENCIAS")}
    for sym in pending:
        groups[classification(sym)].append(sym)
    for group, syms in groups.items():
        (out / f"{group}.txt").write_text("\n".join(syms) + ("\n" if syms else ""), encoding="utf-8")
    result = {
        "etapa": 48,
        "compilacao_boot_publico": compile_status,
        "link_parcial_boot": partial,
        "link_estrito_boot": strict,
        "simbolos_pendentes_objeto": len(pending),
        "simbolos_identificados_log_linker": len(linker),
        "grupos": {k: len(v) for k, v in groups.items()},
        "verificou_jogo_real": False,
        "inclui_codigo_comercial": False,
        "gerou_pkg": False,
        "observacao": "AOT do jogo, dados e renderizacao original NAO incluidos. Compilar nx::boot != executar Castlevania."
    }
    (out / "RESUMO.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "STATUS.txt").write_text(f"COMPILAR_BOOT_CPP={compile_status}\nLINK_PARCIAL_BOOT={partial}\nLINK_ESTRITO_BOOT={strict}\n", encoding="utf-8")
    report = [
        "KAZUMA PORT GAMES BR - ETAPA 48 - BOOT DO RUNTIME PUBLICO",
        "========================================================",
        "COMPILAR_BOOT_CPP=" + compile_status,
        "LINK_PARCIAL_BOOT=" + partial,
        "LINK_ESTRITO_BOOT=" + strict,
        f"PENDENCIAS_NO_OBJETO={len(pending)}",
        "CONTAGENS_POR_GRUPO:",
        *[f"  {k}={len(v)}" for k, v in groups.items()],
        f"SIMBOLOS_NO_LOG_LIMITADO={len(linker)}",
        "",
        "BLOQUEIOS DE GAME DETECTADOS (se houver):",
        *["  " + s for s in groups["MODULOS_DO_JOGO_AUSENTES"][:16]],
        "",
        "PASSOS REAIS APOS ESTA ETAPA:",
        "1. Resolver as APIs PS4 pendentes; nao falsificar implementacoes.",
        "2. Gerar localmente (a partir de copia legitima) os modulos AOT do jogo; NAO subir ExeFS/RomFS ao GitHub publico.",
        "3. Ligar as unidades AOT com nx::boot e validar as dependencias restantes.",
        "4. Somente apos executavel legitimo e inicializacao: testar renderizacao, audio e desempenho.",
        "",
        "AVISO: Check verde = diagnostico concluido, NAO jogo portado, NEM ELF obrigatoriamente produzido.",
    ]
    (out / "LEIA_PRIMEIRO.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("output", type=Path)
    a.add_argument("--compile", required=True, choices=["PASSOU", "FALHOU"])
    a.add_argument("--partial", required=True, choices=["PASSOU", "FALHOU", "NAO_TENTADO"])
    a.add_argument("--strict", required=True, choices=["FALHOU", "PASSOU_ELF_INTERMEDIARIO", "NAO_TENTADO"])
    args = a.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    analyze(args.output, args.compile, args.partial, args.strict)
