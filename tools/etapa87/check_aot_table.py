#!/usr/bin/env python3
"""Etapa 87 — valida tabela AOT sem copiar C++ comercial para o GitHub.

Garante que a tabela de funções declarada pelo recompilador é completa,
sem endereços duplicados, e referencia funções com nomes coerentes.
NÃO compila nem prova que existe jogo executável.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

HEADER = re.compile(r"^functions\s+(\d+),\s*handled\s+(\d+),\s*unhandled\s+(\d+)", re.M)
TABLE = re.compile(r"static const nx::FuncEntry funcs\[\]\s*=\s*\{(.*?)\};", re.S)
ENTRY = re.compile(r"\{\s*(0x[0-9a-fA-F]+)\s*,\s*([A-Za-z_][\w]*)\s*\}\s*,")
EXPECTED_MODULES = {"main", "sdk", "subsdk0"}


def verify_table(table: str, report: str, module: str) -> dict:
    if module not in EXPECTED_MODULES:
        raise ValueError("Nome de módulo inesperado")
    header, block = HEADER.search(report), TABLE.search(table)
    if not header or not block:
        raise ValueError("Relatório ou tabela AOT não reconhecido")
    expected = int(header.group(1))
    entries = ENTRY.findall(block.group(1))
    if len(entries) != expected or expected < 1:
        raise ValueError("Número de entradas difere do total de funções do relatório")
    rest = ENTRY.sub("", block.group(1))
    if rest.strip():
        raise ValueError("Entradas não reconhecidas na tabela")
    offsets = []
    for off, symbol in entries:
        value = int(off, 16)
        if not re.fullmatch(re.escape(module) + r"_[0-9A-Fa-f]+", symbol):
            raise ValueError("Símbolo não pertence ao módulo")
        if int(symbol.rsplit("_", 1)[1], 16) != value:
            raise ValueError("Offset e nome de função diferentes")
        offsets.append(value)
    if offsets != sorted(set(offsets)):
        raise ValueError("Offsets duplicados ou fora de ordem")
    if not re.search(r"extern\s+const\s+nx::ModuleInfo\s+nx_module_" +
                     re.escape(module) + r"\s*=", table):
        raise ValueError("Metadados nx_module ausentes")
    return {
        "etapa": 87,
        "module": module,
        "expected_function_count": expected,
        "table_function_count": len(entries),
        "distinct_function_offsets": len(set(offsets)),
        "first_offset": hex(offsets[0]),
        "last_offset": hex(offsets[-1]),
        "table_consistent": True,
        "handled_reported": int(header.group(2)),
        "unhandled_reported": int(header.group(3)),
        "linked_to_runtime": False,
        "eboot_created": False,
        "pkg_created": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Checar metadados da tabela AOT local, sem publicá-la")
    ap.add_argument("--table", type=Path, required=True)
    ap.add_argument("--aot-report", type=Path, required=True)
    ap.add_argument("--module", choices=sorted(EXPECTED_MODULES), required=True)
    ap.add_argument("--json-report", type=Path)
    args = ap.parse_args()
    result = verify_table(
        args.table.read_text(encoding="utf-8"),
        args.aot_report.read_text(encoding="utf-8"),
        args.module
    )
    output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.json_report:
        if args.json_report.is_symlink() or ".git" in args.json_report.resolve().parts:
            ap.error("Não salvar diagnóstico privado dentro de Git ou via symlink")
        args.json_report.write_text(output, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
