#!/usr/bin/env python3
"""Etapa 86 — link parcial PRIVADO de objetos PS4 já recompilados.

Publica apenas metadados: nunca objetos ELF ou código derivado do jogo.
Usar somente backups privados legítimos. Não gera eboot nem PKG.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tarfile
import tempfile

EXPECTED_SOURCE = "0320bad0c5c3ba5d2571534f47e27be8be2830d803d306bf20d735911491ef1e"
PIN = "4043f21bb4f656d34cd17ba070238c7728d00631"
PATTERN = re.compile(r"code_(\d{3})\.o\Z")


def inspect_archives(archives: list[Path], dest: Path, count: int = 73,
                     source_sha: str = EXPECTED_SOURCE) -> dict:
    names: set[str] = set()
    total_bytes = 0
    if not archives:
        raise ValueError("Nenhum arquivo tar.gz fornecido")
    for path in archives:
        if path.is_symlink() or not path.is_file():
            raise ValueError("Backup ausente, não regular ou link simbólico")
        with tarfile.open(path, "r:gz") as archive:
            members = archive.getmembers()
            manifests = [m for m in members if m.name == "manifest.json" and m.isfile()]
            if len(manifests) != 1 or len(members) > count + 1:
                raise ValueError("Manifesto ausente/duplicado ou arquivo excessivo")
            manifest = json.loads(archive.extractfile(manifests[0]).read())
            if manifest.get("pin") != PIN:
                raise ValueError("Commit do upstream não confere")
            expected = manifest.get("source_archive_sha256", manifest.get("archive_sha256"))
            if expected != source_sha:
                raise ValueError("Origem da recompilação diferente")
            checksums = manifest.get("sha256")
            if not isinstance(checksums, dict):
                raise ValueError("Hashes individuais ausentes")
            for member in members:
                if member.name == "manifest.json":
                    continue
                match = PATTERN.fullmatch(member.name)
                if not match or not member.isfile() or member.name in names:
                    raise ValueError("Arquivo de objeto inválido/duplicado no tar")
                index = int(match.group(1))
                if index >= count or member.size <= 0 or member.size > 30_000_000:
                    raise ValueError("Índice ou tamanho de objeto inválido")
                data = archive.extractfile(member).read()
                if len(data) != member.size or hashlib.sha256(data).hexdigest() != checksums.get(member.name):
                    raise ValueError("SHA256 ou tamanho inválido: " + member.name)
                if (data[:4] != b"\x7fELF" or data[4:6] != b"\x02\x01"
                        or struct.unpack_from("<HH", data, 16) != (1, 62)):
                    raise ValueError("Objeto não é ELF64 x86-64 relocatable")
                (dest / member.name).write_bytes(data)
                names.add(member.name)
                total_bytes += member.size
    if names != {f"code_{i:03}.o" for i in range(count)}:
        raise ValueError("Objetos ausentes — link parcial recusado")
    return {"backups_verificados": len(archives),
            "objetos_validados": len(names),
            "bytes_total_objetos": total_bytes,
            "hashes_manifesto_validos": True}


def run_partial_link(archives: list[Path], count: int = 73,
                     source_sha: str = EXPECTED_SOURCE, linker: str = "ld.lld",
                     nm: str = "nm") -> dict:
    if not shutil.which(linker) or not shutil.which(nm):
        raise ValueError("Linker ou nm não disponível")
    with tempfile.TemporaryDirectory(prefix="kazuma86_private_") as tmp:
        private = Path(tmp)
        result = inspect_archives(archives, private, count, source_sha)
        output = private / "subsdk0_partial.o"
        command = [linker, "-m", "elf_x86_64", "-r", "-o", str(output)]
        command.extend(str(private / f"code_{i:03}.o") for i in range(count))
        process = subprocess.run(command, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, timeout=180, check=False)
        result["partial_link_exit_code"] = process.returncode
        result["partial_link_ok"] = process.returncode == 0 and output.is_file()
        result["undefined_count"] = None
        result["partial_link_bytes"] = None
        if result["partial_link_ok"]:
            result["partial_link_bytes"] = output.stat().st_size
            found = subprocess.run([nm, "-u", str(output)], capture_output=True,
                                   timeout=45, check=False)
            if found.returncode == 0:
                result["undefined_count"] = len(
                    [x for x in found.stdout.decode("utf-8", "replace").splitlines() if x.strip()]
                )
        result.update({
            "etapa": 86,
            "modulo": "subsdk0",
            "link_ps4_com_runtime": False,
            "eboot_gerado": False,
            "pkg_gerado": False,
            "gameplay_testado": False,
            "privado": True,
            "nota": "Link -r é apenas relocável; não verifica execução nem resolve runtime."
        })
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Somente backups privados — sem publicar objetos")
    parser.add_argument("backup_dir", type=Path)
    parser.add_argument("--count", type=int, default=73)
    parser.add_argument("--source-sha", default=EXPECTED_SOURCE)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not 1 <= args.count <= 5000:
        parser.error("Quantidade deve ser 1..5000")
    archives = sorted(args.backup_dir.glob("*objetos_privados.tar.gz"))
    result = run_partial_link(archives, count=args.count, source_sha=args.source_sha)
    safe = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        if args.report.is_symlink() or ".git" in args.report.resolve().parts:
            parser.error("Não gravar relatório dentro do Git ou em symlink")
        args.report.write_text(safe, encoding="utf-8")
    print(safe)
    return 0 if result["partial_link_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
