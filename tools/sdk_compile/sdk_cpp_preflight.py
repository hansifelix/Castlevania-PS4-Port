#!/usr/bin/env python3
"""Preflight local de C++ AOT (SDK) sem exportar conteúdo comercial.

Apenas contagens e nomes genéricos code_XXX.cpp, nunca trechos de código.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import tarfile

CPP = re.compile(r"(?:[^/]+/)*code_(\d{3})\.cpp\Z")


def inspect_archive(path: Path, expected: int = 136, sha256: str | None = None) -> dict:
    if expected < 1 or expected > 3000:
        raise ValueError("Contagem esperada fora da faixa")
    if not path.is_file() or path.is_symlink():
        raise ValueError("Arquivo de backup inválido")
    if sha256:
        h = hashlib.sha256()
        with path.open("rb") as inp:
            for part in iter(lambda: inp.read(1024 * 1024), b""):
                h.update(part)
        if h.hexdigest() != sha256:
            raise ValueError("SHA256 do backup não corresponde")
    names: set[str] = set()
    countl_files = []
    countl_calls = 0
    stg_files = []
    trap_types = Counter()
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        if len(members) > expected + 30:
            raise ValueError("Arquivo contém membros demais")
        for member in members:
            if not member.isfile() or member.issym() or member.islnk():
                raise ValueError("Membro não regular, diretório ou link")
            match = CPP.fullmatch(member.name)
            if not match:
                continue
            name = "code_" + match.group(1) + ".cpp"
            if name in names or member.size > 12_000_000 or member.size < 1:
                raise ValueError("CPP duplicado/inválido")
            names.add(name)
            raw = archive.extractfile(member).read()
            if len(raw) != member.size:
                raise ValueError("CPP truncado")
            source = raw.decode("utf-8")
            zeros = source.count("std::countl_zero(")
            if zeros:
                countl_calls += zeros
                countl_files.append(name)
            if '"stg ' in source:
                stg_files.append(name)
            for m in re.finditer(r'nx::unimpl\([^;]{0,512}?,\s*"([^"\n]+)"\);',
                                 source, re.S):
                reason = m.group(1)
                kind = ("exception_default_guard" if "excepci" in reason else
                        "udf" if reason.startswith("udf") else
                        "undecodable" if reason.startswith("undecodable") else
                        "stg" if reason.startswith("stg") else "other")
                trap_types[kind] += 1
    if names != {f"code_{i:03d}.cpp" for i in range(expected)}:
        raise ValueError("Backup sem todos os C++ esperados")
    return {
        "module": "sdk",
        "code_units": len(names),
        "countl_zero_files": len(countl_files),
        "countl_zero_calls": countl_calls,
        "countl_zero_units": countl_files,
        "stg_units": stg_files,
        "static_unimpl_categories": dict(sorted(trap_types.items())),
        "commercial_source_exported": False,
        "ps4_compiled": False,
        "stg_semantics_implemented": False,
        "runtime_linked": False,
        "pkg_created": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("archive", type=Path)
    p.add_argument("--expected", type=int, default=136)
    p.add_argument("--sha256")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = inspect_archive(args.archive, args.expected, args.sha256)
    output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.is_symlink() or ".git" in args.output.resolve().parts:
            p.error("Não gravar auditoria privada em Git ou via link simbólico")
        args.output.write_text(output, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
