#!/usr/bin/env python3
"""Private-only NSO dynamic-link inspection. Reports counts, never guest code.

No decryption, AOT generation, or PS4 executable. Compressed NSOs require lz4.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

MODULES = ("main", "sdk", "subsdk0")
MAX_IMAGE = 512 * 1024 * 1024
RELOC = {257: "ABS64", 1025: "GLOB_DAT", 1026: "JUMP_SLOT", 1027: "RELATIVE"}


def _image(raw: bytes) -> bytearray:
    if len(raw) < 0x100 or raw[:4] != b"NSO0":
        raise ValueError("Arquivo não é NSO0")
    flags = struct.unpack_from("<I", raw, 12)[0]
    segments = []
    for i in range(3):
        file_off, mem_off, expanded = struct.unpack_from("<III", raw, 0x10 + i * 0x10)
        comp = struct.unpack_from("<I", raw, 0x60 + i * 4)[0]
        stored = comp if flags & (1 << i) else expanded
        if expanded == 0:
            continue
        if file_off < 0x100 or stored == 0 or file_off + stored > len(raw):
            raise ValueError("Segmento NSO ultrapassa o arquivo")
        if mem_off + expanded > MAX_IMAGE:
            raise ValueError("Imagem NSO excede limite de segurança")
        blob = raw[file_off:file_off + stored]
        if flags & (1 << i):
            import lz4.block
            blob = lz4.block.decompress(blob, uncompressed_size=expanded)
        if len(blob) != expanded:
            raise ValueError("Segmento descompactado com tamanho inválido")
        segments.append((mem_off, blob))
    if not segments:
        raise ValueError("NSO sem segmentos")
    size = max(off + len(blob) for off, blob in segments)
    image = bytearray(size)
    for off, blob in segments:
        image[off:off + len(blob)] = blob
    return image


def inspect_module(path: Path, expected: dict | None = None) -> tuple[dict, set[str], set[str], set[str]]:
    if not path.is_file() or path.is_symlink():
        raise ValueError("Módulo ausente ou link simbólico: " + path.name)
    raw = path.read_bytes()
    if expected is not None:
        if hashlib.sha256(raw).hexdigest() != expected["nso_sha256_reference"]:
            raise ValueError("SHA-256 diferente do perfil 1.1.0: " + path.name)
        if raw[0x40:0x60].hex() != expected["build_id"]:
            raise ValueError("Build ID diferente do perfil 1.1.0: " + path.name)
    image = _image(raw)
    size = len(image)
    if size < 32:
        raise ValueError("Imagem pequena demais")
    mod0 = struct.unpack_from("<I", image, 4)[0]
    if mod0 + 24 > size or image[mod0:mod0 + 4] != b"MOD0":
        raise ValueError("MOD0 não encontrado")
    at = mod0 + struct.unpack_from("<i", image, mod0 + 4)[0]
    dynamic = {}
    for _ in range(10000):
        if at < 0 or at + 16 > size:
            raise ValueError("Tabela .dynamic fora da imagem")
        tag, value = struct.unpack_from("<qQ", image, at)
        at += 16
        if tag == 0:
            break
        dynamic.setdefault(tag, value)
    else:
        raise ValueError("Tabela .dynamic sem terminador")
    symtab, strtab, syment = dynamic.get(6), dynamic.get(5), dynamic.get(11, 24)
    if (symtab is None or strtab is None or syment != 24 or strtab < symtab
            or strtab > size or (strtab - symtab) % 24):
        raise ValueError("Tabela de símbolos inválida")
    imported, defined, weak_imported = set(), set(), set()
    for pos in range(symtab, strtab, 24):
        name_off, info, _, shndx, _, _ = struct.unpack_from("<IBBHQQ", image, pos)
        if name_off == 0:
            continue
        start = strtab + name_off
        if start >= size:
            raise ValueError("Índice de símbolo ultrapassa imagem")
        stop = image.find(b"\x00", start, min(start + 1025, size))
        if stop < 0:
            raise ValueError("Nome de símbolo sem terminador")
        name = bytes(image[start:stop]).decode("utf-8", "replace")
        if name:
            (imported if shndx == 0 else defined).add(name)
            if shndx == 0 and info >> 4 == 2:
                weak_imported.add(name)
    types = Counter()
    rela_entries = 0
    for start_tag, length_tag in ((7, 8), (23, 2)):
        start, nbytes = dynamic.get(start_tag), dynamic.get(length_tag, 0)
        if start is None:
            continue
        if nbytes % 24 or start + nbytes > size:
            raise ValueError("Tabela RELA inválida")
        for pos in range(start, start + nbytes, 24):
            _, info, _ = struct.unpack_from("<QQq", image, pos)
            types[RELOC.get(info & 0xffffffff, str(info & 0xffffffff))] += 1
            rela_entries += 1
    relr_count = 0
    if 36 in dynamic:
        start, nbytes = dynamic[36], dynamic.get(35, 0)
        if dynamic.get(37) != 8 or nbytes % 8 or start + nbytes > size:
            raise ValueError("Tabela RELR inválida")
        anchor = False
        for pos in range(start, start + nbytes, 8):
            entry = struct.unpack_from("<Q", image, pos)[0]
            if entry & 1 == 0:
                relr_count += 1
                anchor = True
            elif not anchor:
                raise ValueError("Bitmap RELR sem âncora")
            else:
                relr_count += (entry >> 1).bit_count()
        types["RELATIVE_RELR"] += relr_count
    metadata = {
        "module": path.name,
        "nso_bytes": len(raw),
        "flat_image_bytes": size,
        "dynamic_symbols": (strtab - symtab) // 24,
        "imported_unique": len(imported),
        "imported_weak_unique": len(weak_imported),
        "exported_unique": len(defined),
        "rela_entries": rela_entries,
        "relr_entries": relr_count,
        "relocation_types": dict(sorted(types.items())),
        "unknown_relocation_types": sorted(
            key for key in types
            if key not in {"ABS64", "GLOB_DAT", "JUMP_SLOT", "RELATIVE", "RELATIVE_RELR"}
        ),
    }
    return metadata, imported, defined, weak_imported


def inspect_exefs(folder: Path, profile: dict | None = None) -> dict:
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("ExeFS deve ser pasta normal")
    expected = {}
    if profile:
        items = profile.get("modules")
        if not isinstance(items, list) or {x.get("name") for x in items} != set(MODULES):
            raise ValueError("Perfil sem exatamente main, sdk e subsdk0")
        expected = {item["name"]: item for item in items}
    details, imported, defined, weak_imported = {}, {}, {}, {}
    for name in MODULES:
        details[name], imported[name], defined[name], weak_imported[name] = inspect_module(
            folder / name, expected.get(name))
    all_imports = set.union(*imported.values())
    all_defined = set.union(*defined.values())
    linkage = {}
    for name in MODULES:
        others = set.union(*(defined[n] for n in MODULES if n != name))
        missing = imported[name] - others
        linkage[name] = {
            "imports_unique": len(imported[name]),
            "imports_resolved_other_module": len(imported[name] & others),
            "imports_not_defined_other_module": len(missing),
            "unresolved_weak_imports": len(missing & weak_imported[name]),
            "unresolved_nonweak_imports": len(missing - weak_imported[name]),
        }
    return {
        "etapa": 78,
        "profile_matched": bool(profile),
        "modules": details,
        "linkage": linkage,
        "unique_imports": len(all_imports),
        "imports_resolved_in_exefs": len(all_imports & all_defined),
        "imports_without_exefs_definition": len(all_imports - all_defined),
        "imports_without_exefs_definition_nonweak": len(
            set.union(*(imported[n] - defined[n] - weak_imported[n]
                        for n in MODULES)) - all_defined),
        "unresolved_names_exported": False,
        "aot_generated": False,
        "ps4_boot_tested": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("exefs", type=Path)
    parser.add_argument("--profile", type=Path, default=(
        Path(__file__).resolve().parents[1] / "etapa77" / "upstream_build_1_1_0.json"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = inspect_exefs(args.exefs, json.loads(args.profile.read_text(encoding="utf-8")))
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        if args.report.is_symlink():
            parser.error("Relatório não pode ser um link simbólico")
        args.report.write_text(payload, encoding="utf-8")
    print(payload)
    return 0 if all(not m["unknown_relocation_types"] for m in report["modules"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
