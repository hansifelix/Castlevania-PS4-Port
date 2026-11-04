#!/usr/bin/env python3
"""Verifica localmente cabeçalhos NSO do ExeFS, sem ler/exportar código do jogo.

Não descriptografa NSP/NCA, não verifica automaticamente versão 1.1.0 e não gera AOT.
Os três módulos vêm de uma extração privada e autorizada.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct

MODULES = ("main", "sdk", "subsdk0")
HEADER_SIZE = 0x100


def inspect_module(path: Path) -> dict:
    """Inspeciona só os 256 bytes de cabeçalho e tamanho do arquivo."""
    if not path.is_file() or path.is_symlink():
        return {"ok": False, "motivo": "ausente ou não é arquivo regular"}
    size = path.stat().st_size
    if size < HEADER_SIZE:
        return {"ok": False, "motivo": "arquivo menor que cabeçalho NSO"}
    with path.open("rb") as f:
        head = f.read(HEADER_SIZE)
    if head[:4] != b"NSO0":
        return {"ok": False, "motivo": "assinatura NSO0 ausente (verifique ExeFS descriptografado)"}
    flags = struct.unpack_from("<I", head, 0x0C)[0]
    segments = []
    for i, name in enumerate(("text", "rodata", "data")):
        base = (0x10, 0x20, 0x30)[i]
        offset, _memory_offset, expanded = struct.unpack_from("<III", head, base)
        compressed = struct.unpack_from("<I", head, 0x60 + 4 * i)[0]
        stored = compressed if flags & (1 << i) else expanded
        if expanded > 0 and (stored == 0 or offset < HEADER_SIZE or offset + stored > size):
            return {"ok": False, "motivo": f"segmento {name} ultrapassa arquivo ou tem tamanho inválido"}
        segments.append({"nome": name, "comprimido": bool(flags & (1 << i)), "bytes_armazenados": stored})
    return {
        "ok": True,
        "formato": "NSO0",
        "bytes": size,
        "build_id": head[0x40:0x60].hex(),
        "segmentos": segments,
    }


def inspect_exefs(folder: Path, expected: dict | None = None) -> dict:
    modules = {name: inspect_module(folder / name) for name in MODULES}
    valid = all(v["ok"] for v in modules.values())
    if expected is not None:
        if set(expected) != set(MODULES):
            raise ValueError("Esperados build IDs para main, sdk e subsdk0")
        for name, item in modules.items():
            ref = expected[name]
            if not isinstance(ref, str) or len(ref) != 64 or any(c not in '0123456789abcdefABCDEF' for c in ref):
                raise ValueError("Build ID esperado inválido para " + name)
            item["build_id_confere"] = bool(item["ok"] and item["build_id"] == ref.lower())
        valid = valid and all(item["build_id_confere"] for item in modules.values())
    return {
        "etapa": 76,
        "checagem_local": True,
        "modulos": modules,
        "entradas_exefs_validas": valid,
        "build_ids_conferidos": expected is not None,
        "versao_1_1_0_verificada": False,  # requer vínculo confiável entre IDs e build oficial
        "romfs_validada": False,
        "aot_compilado": False,
        "boot_ps4_testado": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspecionar ExeFS privado sem publicar módulos.")
    parser.add_argument("exefs", type=Path, help="pasta que contém main, sdk e subsdk0")
    parser.add_argument("--expected-build-ids", type=Path, help="JSON LOCAL com build IDs esperados, se verificados independentemente")
    parser.add_argument("--report", type=Path, help="JSON local (somente metadados, nenhum byte do jogo)")
    args = parser.parse_args()
    try:
        expected = json.loads(args.expected_build_ids.read_text(encoding="utf-8")) if args.expected_build_ids else None
        report = inspect_exefs(args.exefs, expected)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    if args.report:
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("EXEFS_LOCAL=" + ("OK" if report["entradas_exefs_validas"] else "BLOQUEADO"))
    for name, item in report["modulos"].items():
        print(f"{name}: " + ("NSO0 válido estruturalmente" if item["ok"] else item["motivo"]))
    print("AVISO: formato NSO válido NÃO confirma revisão 1.1.0 nem recompilação AOT.")
    return 0 if report["entradas_exefs_validas"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
