#!/usr/bin/env python3
"""Etapa 79: executar AOT original somente com os três NSOs locais validados.

Requer Python 3.10+, capstone e lz4, checkout do upstream fixado.
Não publica C++ gerado, binários, ROM ou chaves. Nunca gera PKG.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.etapa81.aot_report_gate import parse_report

MODULES = ("subsdk0", "sdk", "main")
PINNED = "4043f21bb4f656d34cd17ba070238c7728d00631"
PROFILE = Path(__file__).resolve().parents[1] / "etapa77" / "upstream_build_1_1_0.json"
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def is_under_repo(path: Path) -> bool:
    for parent in (path, *path.parents):
        if (parent / ".git").exists():
            return True
    return False


def check_output(out: Path, exefs: Path, upstream: Path) -> None:
    # Never write private generated sources into a versioned/public checkout.
    candidate = out.resolve()
    if any(candidate == p.resolve() or p.resolve() in candidate.parents
           for p in (exefs, upstream)):
        raise ValueError("Saída dentro do ExeFS ou checkout upstream não permitida")
    if is_under_repo(candidate):
        raise ValueError("Saída sob Git: escolha diretório temporário PRIVADO fora do repositório")
    if out.exists() and (out.is_symlink() or any(out.iterdir())):
        raise ValueError("Saída deve estar ausente ou ser diretório vazio, sem link simbólico")


def validate_input(exefs: Path, module: str, profile: dict) -> dict:
    if module not in MODULES:
        raise ValueError("Módulo desconhecido")
    if not exefs.is_dir() or exefs.is_symlink():
        raise ValueError("ExeFS deve ser uma pasta real")
    specs = {x["name"]: x for x in profile["modules"]}
    expected = specs[module]
    path = exefs / module
    if not path.is_file() or path.is_symlink():
        raise ValueError("Módulo privado ausente ou link simbólico")
    with path.open("rb") as f:
        header = f.read(0x100)
    if len(header) != 0x100 or header[:4] != b"NSO0":
        raise ValueError("Cabeçalho NSO0 inválido")
    if header[0x40:0x60].hex() != expected["build_id"]:
        raise ValueError("Build ID não confere com a revisão 1.1.0")
    if digest(path) != expected["nso_sha256_reference"]:
        raise ValueError("SHA256 não confere com a revisão 1.1.0")
    return expected


def upstream_checked(upstream: Path) -> None:
    if not (upstream / "recomp" / "__main__.py").is_file():
        raise ValueError("Recompilador upstream não encontrado")
    try:
        actual = subprocess.check_output(
            ["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True, timeout=10).strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ValueError("Não foi possível confirmar commit upstream") from exc
    if actual != PINNED:
        raise ValueError("Commit upstream diferente do fixado: recusado")


def build_command(python: str, exefs: Path, out: Path, upstream: Path,
                  module: str, base: str, entry: str | None) -> list[str]:
    command = [python, "-m", "recomp", str(exefs / module), str(out),
               "--name", module, "--base", base, "--exceptions"]
    if module == "main":
        patch = upstream / "games" / "castlevania" / "resolution-patches.json"
        if not patch.is_file():
            raise ValueError("Patches específicos de main ausentes")
        command += ["--patches", str(patch)]
    if entry:
        if not re.fullmatch(r"0x[0-9a-fA-F]+", entry):
            raise ValueError("--only-entry exige hexadecimal, exemplo 0x20")
        command += ["--only", entry]
    return command


def main() -> int:
    ap = argparse.ArgumentParser(description="AOT privado (sem upload de material comercial)")
    ap.add_argument("--exefs", required=True, type=Path)
    ap.add_argument("--upstream", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--module", choices=MODULES, default="subsdk0")
    ap.add_argument("--only-entry", help="Diagnóstico: gera apenas função escolhida (AOT incompleto)")
    ap.add_argument("--timeout", type=int, default=3600, help="Segundos, 1..14400")
    args = ap.parse_args()
    if not 1 <= args.timeout <= 14400:
        ap.error("--timeout deve estar entre 1 e 14400")
    exefs, upstream, out = (p.expanduser().resolve() for p in
                            (args.exefs, args.upstream, args.out))
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    if profile.get("content_version") != "1.1.0":
        ap.error("Perfil 1.1.0 ausente")
    try:
        upstream_checked(upstream)
        expected = validate_input(exefs, args.module, profile)
        check_output(out, exefs, upstream)
        # The public recompiler uses the same verified source for local input only.
        cmd = build_command(sys.executable, exefs, out, upstream,
                            args.module, expected["base"] if "base" in expected else
                            {"main": "0x4000000000", "sdk": "0x4010000000",
                             "subsdk0": "0x4020000000"}[args.module], args.only_entry)
        out.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(upstream) + os.pathsep + env.get("PYTHONPATH", "")
        with (out / "aot.stdout.txt").open("w") as stdout, (out / "aot.stderr.txt").open("w") as stderr:
            try:
                proc = subprocess.run(cmd, env=env, cwd=upstream, timeout=args.timeout,
                                      stdout=stdout, stderr=stderr, check=False)
                returncode = proc.returncode
                error = None
            except subprocess.TimeoutExpired:
                returncode, error = 124, "TIMEOUT"
        report_txt = out / "report.txt"
        report = report_txt.read_text(encoding="utf-8", errors="replace") if report_txt.is_file() else ""
        cpp_files = list(out.glob("code_*.cpp"))
        success = (returncode == 0 and (out / "funcs.h").is_file() and
                   (out / "table.cpp").is_file() and report_txt.is_file()
                   and len(cpp_files) > 0)
        coverage = parse_report(report) if report else None
        # AOT emitido pode conter instruções sem handler, caso do STG no SDK.
        # Não declarar que o resultado está pronto para link só porque o processo retornou 0.
        summary = {
            "etapa": 79,
            "module": args.module,
            "input_nso_sha256_verified": True,
            "upstream_commit_verified": PINNED,
            "exit_code": returncode,
            "timeout": error == "TIMEOUT",
            "aot_generated": success,
            "aot_instruction_coverage": coverage,
            "all_instructions_supported": bool(coverage and coverage["all_instructions_supported"]),
            "aot_has_runtime_traps": bool(coverage and coverage["instructions_unhandled"]),
            "aot_partial_only_entry": bool(args.only_entry),
            "generated_code_translation_units": len(cpp_files),
            "report_first_line": report.splitlines()[0][:240] if report else "",
            "compiled_for_ps4": False,
            "linked_ps4": False,
            "game_boot_ps4": False,
            "contains_private_generated_code_in_output": success,
        }
        (out / "etapa79_local.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in summary.items()
                          if k != "contains_private_generated_code_in_output"},
                         ensure_ascii=False, indent=2))
        print("ATENÇÃO: a pasta de saída tem dados derivados do jogo; não envie ao GitHub.")
        return 0 if success else 1
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        ap.error(str(exc))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
