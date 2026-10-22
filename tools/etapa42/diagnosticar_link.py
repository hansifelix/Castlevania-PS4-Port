#!/usr/bin/env python3
"""Etapa 42: classifica erros de link reais (sem forcar simbolos, sem jogo)."""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import re

# ld.lld emite linhas "ld.lld: error: undefined symbol: <simbolo>"
UNDEFINED = re.compile(r"(?:error:\s*)?undefined symbol:\s*(.+)$")
DUPLICATE = re.compile(r"(?:error:\s*)?duplicate symbol:\s*(.+)$")
MISSING_LIB = re.compile(r"(?:unable to find library|cannot open)\s+(.+)$", re.I)


def unique_errors(log: str) -> dict[str, list[str]]:
    grupos: dict[str, set[str]] = {
        "simbolos_indefinidos": set(),
        "simbolos_duplicados": set(),
        "bibliotecas_ausentes": set(),
        "outros_erros": set(),
    }
    for line in log.splitlines():
        line = line.strip()
        # Rejeitar referencias do tipo ">>> referenced by"; uma so causa pode ocorrer varias vezes.
        if m := UNDEFINED.search(line):
            grupos["simbolos_indefinidos"].add(m.group(1).strip())
        elif m := DUPLICATE.search(line):
            grupos["simbolos_duplicados"].add(m.group(1).strip())
        elif m := MISSING_LIB.search(line):
            grupos["bibliotecas_ausentes"].add(m.group(1).strip())
        elif "error:" in line or "fatal error:" in line:
            # Nem toda falha vem de simbolo indefinido (ABI, relocacoes, etc.)
            grupos["outros_erros"].add(line[:500])
    return {nome: sorted(valores) for nome, valores in grupos.items()}


def gerar(diretorio: Path, status: str, baseline: str, sdk_libs: list[str]) -> dict:
    log_path = diretorio / "LINK_EXECUTAVEL.log"
    if not log_path.is_file():
        raise FileNotFoundError(f"Arquivo de link inexistente: {log_path}")
    log = log_path.read_text(encoding="utf-8", errors="replace")
    grupos = unique_errors(log)
    rel41_path = Path("relatorios/etapa41/RESULTADO_ETAPA41.txt")
    rel41 = rel41_path.read_text(encoding="utf-8") if rel41_path.is_file() else ""
    info = {
        "etapa": 42,
        "tipo": "link ELF estrito com runtime publico e bibliotecas OpenOrbis",
        "resultado_link": status,
        "baseline_homebrew_sdk": baseline,
        "bibliotecas_passadas_ao_linker": sdk_libs,
        "simbolos_indefinidos_identificados_no_log": len(grupos["simbolos_indefinidos"]),
        "simbolos_duplicados_identificados_no_log": len(grupos["simbolos_duplicados"]),
        "bibliotecas_ausentes_identificadas_no_log": len(grupos["bibliotecas_ausentes"]),
        "log_pode_estar_limitado_pelo_linker": True,
        "runtime_execucao_ps4_comprovada": False,
        "jogo_incluido": False,
        "gerou_pkg": False,
        "nota": (
            "Um check verde significa que o diagnostico executou corretamente; "
            "NAO significa que o link produziu um executavel. "
            "O objeto da Etapa 41 e parcialmente relocavel."
        ),
    }
    (diretorio / "RESUMO.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    for nome, linhas in grupos.items():
        (diretorio / f"{nome.upper()}.txt").write_text(
            "\n".join(linhas) + ("\n" if linhas else ""), encoding="utf-8"
        )
    texto = [
        "KAZUMA / ETAPA 42 - LINK EXECUTAVEL E DIAGNOSTICO",
        "==============================================",
        f"LINK_EXECUTAVEL={status}",
        f"BASELINE_HOME_BREW={baseline}",
        f"BIBLIOTECAS={' '.join(sdk_libs)}",
        *[f"{k.upper()}={len(v)}" for k, v in grupos.items()],
        "ATENCAO: contagem no log nao substitui os 270 simbolos da Etapa 41; o linker pode limitar as mensagens.",
        "SEM arquivos comerciais, SEM PKG, SEM teste no PS4.",
        "",
        "RESUMO DA ETAPA 41 (REFERENCIA):",
        rel41.strip() if rel41 else "relatorio da Etapa 41 indisponivel",
    ]
    (diretorio / "LEIA_PRIMEIRO.txt").write_text("\n".join(texto) + "\n", encoding="utf-8")
    return info


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("diretorio", type=Path)
    p.add_argument("--status", choices=["SUCESSO_ELF_INTERMEDIARIO", "FALHOU_LINK_ESTRITO"], required=True)
    p.add_argument("--baseline", choices=["PASSOU", "FALHOU"], required=True)
    p.add_argument("--libs", default="")
    a = p.parse_args()
    info = gerar(a.diretorio, a.status, a.baseline, a.libs.split())
    print(f"ETAPA42: link = {info['resultado_link']}; baseline = {info['baseline_homebrew_sdk']}")
    print(f"Simbolos indefinidos distintos no log: {info['simbolos_indefinidos_identificados_no_log']}")
    print("ATENCAO: diagnostico aprovado nao equivale a ELF executavel ou jogo rodando.")
