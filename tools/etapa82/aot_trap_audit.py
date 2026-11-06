#!/usr/bin/env python3
"""Etapa 82: auditoria local, sem publicar C++ derivado do jogo.

O relatorio upstream 'unhandled 0' não garante ausência de chamadas nx::unimpl
no código gerado (por exemplo, UDF/bytes indecodáveis).
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

CALL = re.compile(r"\bnx::unimpl\s*\((?P<call>[^;]{0,2048}?)\)\s*;", re.DOTALL)
WHY = re.compile(r',\s*"([^"\n]{1,300})"\s*$')
OFFSET = re.compile(r"\bNXB\s*\+\s*0x([0-9a-fA-F]+)")
LIMIT_EXAMPLES = 12


def audit_cpp(directory: Path, expected_units: int | None = None) -> dict:
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError("Pasta AOT ausente ou link simbólico")
    files = sorted(directory.glob("code_*.cpp"))
    if not files or (expected_units is not None and len(files) != expected_units):
        raise ValueError("Quantidade de unidades C++ ausente ou diferente do relatório")
    reasons: Counter[str] = Counter()
    file_counts = {}
    samples = []
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise ValueError("Unidade C++ não é arquivo regular")
        # Abre uma unidade por vez; main pode ter centenas de MB de código total.
        source = path.read_text(encoding="utf-8", errors="replace")
        local = 0
        for m in CALL.finditer(source):
            local += 1
            params = m.group("call")
            why = WHY.search(params)
            reason = why.group(1) if why else "nao_classificado"
            if reason.startswith("undecodable"):
                category = "undecodable"
            elif reason.startswith("udf"):
                category = "udf"
            else:
                category = "other"
            reasons[category] += 1
            if len(samples) < LIMIT_EXAMPLES:
                offset = OFFSET.search(params)
                samples.append({
                    "unidade": path.name,
                    "categoria": category,
                    "deslocamento_guest_hex": "0x" + offset.group(1).lower() if offset else None,
                })
        if local:
            file_counts[path.name] = local
    total = sum(reasons.values())
    return {
        "etapa": 82,
        "generated_code_translation_units_audited": len(files),
        "nx_unimpl_calls": total,
        "categories": dict(sorted(reasons.items())),
        "cpp_units_with_traps": len(file_counts),
        "samples_metadata_only": samples,
        "no_unimpl_calls_detected": total == 0,
        "all_paths_reachable": None,  # Análise estática não prova alcançabilidade!
        "compiled_for_ps4": False,
        "linked_ps4": False,
        "game_boot_ps4": False,
        "commercial_code_exported": False,
        "notes": (
            "Uma chamada nx::unimpl pode estar em caminho inalcançável/dados confundidos "
            "com instruções; número não representa falhas observadas em runtime. "
            "unhandled 0 do upstream não é prova de ausência dessas chamadas."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventariar traps no AOT privado (metadados apenas).")
    parser.add_argument("aot", type=Path)
    parser.add_argument("--expected-units", type=int)
    parser.add_argument("--report", type=Path, help="JSON privado com contagens, sem conteúdo do jogo")
    args = parser.parse_args()
    result = audit_cpp(args.aot, args.expected_units)
    data = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        if args.report.is_symlink():
            parser.error("Destino de relatório é link simbólico")
        args.report.write_text(data, encoding="utf-8")
    print(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
