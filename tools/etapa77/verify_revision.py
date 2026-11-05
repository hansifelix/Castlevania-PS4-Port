#!/usr/bin/env python3
"""Confere ExeFS privado com hashes da revisão exigida pelo upstream.

Não extrai, descriptografa, recompila, faz upload, nem lê além do necessário
para calcular SHA256. Use somente módulos obtidos legitimamente.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.etapa76.exefs_preflight import MODULES, inspect_module

REFERENCE = Path(__file__).with_name("upstream_build_1_1_0.json")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def load_profile(path: Path) -> dict:
    profile = json.loads(path.read_text(encoding="utf-8"))
    if profile.get("content_version") != "1.1.0":
        raise ValueError("O perfil deve declarar content_version 1.1.0")
    entries = profile.get("modules")
    if not isinstance(entries, list) or len(entries) != len(MODULES):
        raise ValueError("O perfil deve listar exatamente os três módulos")
    if {x.get("name") for x in entries if isinstance(x, dict)} != set(MODULES):
        raise ValueError("Nomes dos módulos não correspondem a main, sdk e subsdk0")
    for item in entries:
        for key in ("build_id", "nso_sha256_reference"):
            value = item.get(key)
            if not isinstance(value, str) or not _HEX64.fullmatch(value):
                raise ValueError(f"Valor hexadecimal inválido: {item['name']}.{key}")
    return profile


def sha256_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            sha.update(chunk)
    return sha.hexdigest()


def verify_exefs(folder: Path, profile: dict) -> dict:
    """Cheque estrutural e SHA256 dos NSO originais. Nunca assume versão por nome."""
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("A pasta ExeFS deve existir e não pode ser um link simbólico")
    # Validate user-supplied profiles too (used by synthetic tests).
    modules = profile.get("modules")
    if not isinstance(modules, list) or len(modules) != 3:
        raise ValueError("Perfil incompleto")
    entries = {m.get("name"): m for m in modules if isinstance(m, dict)}
    if set(entries) != set(MODULES):
        raise ValueError("Perfil contém módulos inválidos ou duplicados")
    results = {}
    for name in MODULES:
        metadata = inspect_module(folder / name)
        expected = entries[name]
        if metadata["ok"]:
            digest = sha256_file(folder / name)
            header_matches = metadata["build_id"] == expected["build_id"]
            checksum_matches = digest == expected["nso_sha256_reference"]
            results[name] = {
                "formato_nso": "OK",
                "bytes": metadata["bytes"],
                "build_id_confere": header_matches,
                "sha256_nso_confere": checksum_matches,
                "identidade_confirmada": header_matches and checksum_matches,
            }
        else:
            results[name] = {
                "formato_nso": "INVALIDO_OU_AUSENTE",
                "motivo": metadata["motivo"],
                "build_id_confere": False,
                "sha256_nso_confere": False,
                "identidade_confirmada": False,
            }
    return {
        "etapa": 77,
        "perfil_content_version": profile["content_version"],
        "referencia": profile.get("source_commit", "não especificada"),
        "modulos": results,
        "correspondencia_exata_ao_perfil": all(x["identidade_confirmada"] for x in results.values()),
        "observacao": (
            "Checa somente hashes de NSO e build IDs. Um NSO reempacotado pode "
            "ter SHA diferente mesmo com imagem equivalente; isso não comprova "
            "que a versão é incompatível. Sem verificação de imagem descomprimida, "
            "RomFS ou compilação AOT."
        ),
        "recompilacao_aot_feita": False,
        "romfs_validada": False,
        "executado_ps4": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Comparar ExeFS privado com perfil público Castlevania 1.1.0."
    )
    ap.add_argument("exefs", type=Path, help="Pasta PRIVADA contendo main, sdk e subsdk0")
    ap.add_argument("--report", type=Path, help="Salvar somente metadados JSON localmente")
    args = ap.parse_args()
    try:
        report = verify_exefs(args.exefs, load_profile(REFERENCE))
        if args.report:
            if args.report.is_symlink():
                raise ValueError("Relatório não pode ser gravado em link simbólico")
            args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                   encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as err:
        ap.error(str(err))
    for name, details in report["modulos"].items():
        print(f"{name}: " + ("CONFERE" if details["identidade_confirmada"] else
                            "NÃO CONFIRMADO"))
    print("EXEFS_PERFIL_1_1_0=" +
          ("CONFERE" if report["correspondencia_exata_ao_perfil"] else "NÃO CONFIRMADO"))
    print("Nenhum arquivo do jogo foi copiado; não verifica RomFS nem gera port/PKG.")
    return 0 if report["correspondencia_exata_ao_perfil"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
