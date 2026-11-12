#!/usr/bin/env python3
"""Read-only integrity audit for private Castlevania AOT object backups.

Scans loose files and ZIP members without extracting or modifying them.
Reports module/index coverage, ELF64 ET_REL x86-64 headers, SHA-256 hashes,
archive member counts, and any readable SHA256SUMS-style manifest matches.
Never compiles, links, uploads, deletes, renames, or rewrites private inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import sys
import zipfile

EXPECTED = {"main": 1707, "sdk": 136, "subsdk0": 73}
OBJECT = re.compile(r"^code_(\d+)\.o$", re.IGNORECASE)
SHA_LINE = re.compile(r"^\s*([0-9a-fA-F]{64})\s+[* ]?(.+?)\s*$")


def module_for(parts: tuple[str, ...]) -> str | None:
    found = set()
    for part in parts:
        token = PurePosixPath(part).name.lower()
        token = re.sub(r"\\.(zip|7z|tar|tgz|gz)$", "", token)
        for module in EXPECTED:
            if token == module or token.startswith(module + "_") or token.startswith(module + "-"):
                found.add(module)
    return next(iter(found)) if len(found) == 1 else None


def elf64_rel_x86_64(header: bytes) -> tuple[bool, str]:
    if len(header) < 64:
        return False, "truncated_elf_header"
    if header[:4] != b"\x7fELF":
        return False, "not_elf"
    if header[4] != 2:
        return False, "not_elf64"
    if header[5] != 1:
        return False, "not_little_endian"
    if header[6] != 1:
        return False, "invalid_elf_version"
    e_type, e_machine, e_version = struct.unpack_from("<HHI", header, 16)
    e_ehsize = struct.unpack_from("<H", header, 52)[0]
    if e_type != 1:
        return False, "not_ET_REL"
    if e_machine != 62:
        return False, "not_x86_64"
    if e_version != 1 or e_ehsize != 64:
        return False, "invalid_elf64_header"
    return True, "ELF64_ET_REL_x86_64"


def digest_stream(stream) -> tuple[str, bytes]:
    h = hashlib.sha256()
    head = stream.read(64)
    h.update(head)
    while True:
        block = stream.read(1024 * 1024)
        if not block:
            break
        h.update(block)
    return h.hexdigest(), head


def parse_manifest(data: bytes) -> dict[str, str]:
    text = data.decode("utf-8", "replace")
    out: dict[str, str] = {}
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        value = None
    if isinstance(value, dict):
        def walk(obj, prefix=""):
            if isinstance(obj, dict):
                for key, child in obj.items():
                    walk(child, f"{prefix}/{key}" if prefix else str(key))
            elif isinstance(obj, list):
                for i, child in enumerate(obj):
                    walk(child, f"{prefix}/{i}")
            elif isinstance(obj, str) and re.fullmatch(r"[0-9a-fA-F]{64}", obj):
                out[prefix.replace("\\", "/").lstrip("./")] = obj.lower()
        walk(value)
        if out:
            return out
    for line in text.splitlines():
        match = SHA_LINE.match(line)
        if match:
            out[match.group(2).strip().replace("\\", "/").lstrip("./")] = match.group(1).lower()
    return out


def is_manifest(name: str) -> bool:
    base = PurePosixPath(name).name.lower()
    return "manifest" in base or base.endswith((".sha256", ".sha256sum", ".sha256sums"))


def safe_report_destination(root: Path, report: Path) -> Path:
    dest = report.expanduser().absolute()
    if dest.is_symlink():
        raise ValueError("Relatório não pode ser link simbólico")
    resolved_root = root.resolve()
    resolved_parent = dest.parent.resolve()
    if resolved_parent == resolved_root or resolved_root in resolved_parent.parents:
        raise ValueError("Relatório deve ficar fora da pasta privada auditada")
    return dest


def audit(root: Path) -> dict:
    root = root.expanduser()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("--root deve ser uma pasta real, sem symlink")
    root = root.resolve()
    objects: dict[str, dict[int, list[dict]]] = {m: {} for m in EXPECTED}
    manifest_entries: dict[str, set[str]] = {}
    manifest_by_module_index: dict[tuple[str, int], set[str]] = {}
    manifest_by_basename: dict[str, set[str]] = {}
    archive_count = 0
    archive_members = 0
    manifests_seen = 0
    manifest_files_with_hashes = 0
    loose_files = 0
    invalid_objects = []
    unreadable_archives = []
    duplicate_archive_names = []

    def record(module: str | None, name: str, sha: str, head: bytes, source: str):
        match = OBJECT.fullmatch(PurePosixPath(name).name)
        if not match or module not in EXPECTED:
            return
        index = int(match.group(1))
        ok, kind = elf64_rel_x86_64(head)
        entry = {
            "index": index,
            "sha256": sha,
            "elf64_et_rel_x86_64": ok,
            "elf_check": kind,
            "source": source,
        }
        objects[module].setdefault(index, []).append(entry)
        if not ok:
            invalid_objects.append({"module": module, "index": index, "source": source, "reason": kind})

    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if zipfile.is_zipfile(path):
            archive_count += 1
            try:
                with zipfile.ZipFile(path) as archive:
                    names = archive.namelist()
                    archive_members += len(names)
                    if len(names) != len(set(names)):
                        duplicate_archive_names.append(rel)
                    for info in archive.infolist():
                        if info.is_dir():
                            continue
                        inner = info.filename.replace("\\", "/")
                        module = module_for(tuple(PurePosixPath(inner).parts)) or module_for(tuple(Path(rel).parts))
                        if is_manifest(inner):
                            manifests_seen += 1
                            try:
                                raw = archive.read(info)
                                parsed = parse_manifest(raw)
                                if parsed:
                                    manifest_files_with_hashes += 1
                                    for k, v in parsed.items():
                                        normalized = k.lower()
                                        manifest_entries.setdefault(normalized, set()).add(v)
                                        basename = PurePosixPath(normalized).name
                                        manifest_by_basename.setdefault(basename, set()).add(v)
                                        manifest_module = module_for(tuple(PurePosixPath(normalized).parts))
                                        manifest_object = OBJECT.fullmatch(basename)
                                        if manifest_module and manifest_object:
                                            key = (manifest_module, int(manifest_object.group(1)))
                                            manifest_by_module_index.setdefault(key, set()).add(v)
                            except (OSError, RuntimeError, zipfile.BadZipFile):
                                pass
                        if OBJECT.fullmatch(PurePosixPath(inner).name) and module:
                            try:
                                with archive.open(info) as stream:
                                    sha, head = digest_stream(stream)
                                record(module, inner, sha, head, f"{rel}::{inner}")
                            except (OSError, RuntimeError, zipfile.BadZipFile):
                                invalid_objects.append({"module": module, "source": f"{rel}::{inner}", "reason": "archive_member_read_failed"})
            except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
                unreadable_archives.append({"archive": rel, "reason": type(exc).__name__})
            continue

        loose_files += 1
        if is_manifest(rel):
            manifests_seen += 1
            try:
                parsed = parse_manifest(path.read_bytes())
                if parsed:
                    manifest_files_with_hashes += 1
                    for k, v in parsed.items():
                        normalized = k.lower()
                        manifest_entries.setdefault(normalized, set()).add(v)
                        basename = PurePosixPath(normalized).name
                        manifest_by_basename.setdefault(basename, set()).add(v)
                        manifest_module = module_for(tuple(PurePosixPath(normalized).parts))
                        manifest_object = OBJECT.fullmatch(basename)
                        if manifest_module and manifest_object:
                            key = (manifest_module, int(manifest_object.group(1)))
                            manifest_by_module_index.setdefault(key, set()).add(v)
            except OSError:
                pass
        module = module_for(tuple(Path(rel).parts))
        if OBJECT.fullmatch(path.name) and module:
            try:
                with path.open("rb") as stream:
                    sha, head = digest_stream(stream)
                record(module, path.name, sha, head, rel)
            except OSError:
                invalid_objects.append({"module": module, "source": rel, "reason": "file_read_failed"})

    module_reports = {}
    all_manifest_checked = 0
    all_manifest_mismatch = []
    total_objects = 0
    total_replicas = 0
    total_conflicts = 0
    all_coverage = True
    all_elf_valid = True

    for module, expected_count in EXPECTED.items():
        indices = objects[module]
        missing = sorted(set(range(expected_count)) - set(indices))
        unexpected = sorted(i for i in indices if i < 0 or i >= expected_count)
        conflicts = []
        replicas = 0
        manifest_checked_indices = set()
        for index, copies in sorted(indices.items()):
            hashes = {item["sha256"] for item in copies}
            if len(hashes) > 1:
                conflicts.append({"index": index, "sha256_variants": sorted(hashes)})
            else:
                replicas += max(0, len(copies) - 1)
            for item in copies:
                width = 4 if module == "main" else 3
                manifest_name = f"code_{index:0{width}d}.o".lower()
                known = manifest_by_module_index.get((module, index), set())
                if not known:
                    fallback = manifest_by_basename.get(manifest_name, set())
                    known = fallback if len(fallback) == 1 else set()
                if item["sha256"] in known:
                    manifest_checked_indices.add(index)
                elif known:
                    all_manifest_mismatch.append({"module": module, "index": index, "source": item["source"]})
        valid_count = sum(
            1 for copies in indices.values()
            for item in copies if item["elf64_et_rel_x86_64"]
        )
        unique_count = len(indices)
        coverage = not missing and not unexpected and not conflicts
        elf_valid = valid_count == sum(len(c) for c in indices.values())
        all_coverage &= coverage
        all_elf_valid &= elf_valid
        total_objects += sum(len(c) for c in indices.values())
        total_replicas += replicas
        total_conflicts += len(conflicts)
        all_manifest_checked += len(manifest_checked_indices)
        module_reports[module] = {
            "expected_indices": f"000..{expected_count-1:0{4 if module == 'main' else 3}d}",
            "unique_indices_found": unique_count,
            "object_copies_found": sum(len(c) for c in indices.values()),
            "missing_indices": missing,
            "unexpected_indices": unexpected,
            "same_hash_backup_replicas": replicas,
            "conflicting_hash_indices": conflicts,
            "elf64_et_rel_x86_64_valid_copies": valid_count,
            "elf_invalid": not elf_valid,
            "manifest_hash_matches_unique_indices": len(manifest_checked_indices),
            "coverage_complete": coverage,
        }

    return {
        "audit_mode": "READ_ONLY_NO_EXTRACT_NO_COMPILE_NO_LINK",
        "input_root": root.name,
        "archives_found": archive_count,
        "archive_members_enumerated": archive_members,
        "loose_files_enumerated": loose_files,
        "manifest_files_found": manifests_seen,
        "manifest_files_with_sha256_entries": manifest_files_with_hashes,
        "manifest_hash_matches": all_manifest_checked,
        "manifest_mismatches": all_manifest_mismatch,
        "duplicate_member_names_in_archives": duplicate_archive_names,
        "unreadable_archives": unreadable_archives,
        "invalid_objects": invalid_objects,
        "module_results": module_reports,
        "totals": {
            "expected_unique_object_indices": sum(EXPECTED.values()),
            "object_copies_found": total_objects,
            "same_hash_backup_replicas": total_replicas,
            "conflicting_hash_indices": total_conflicts,
        },
        "object_index_coverage_complete": all_coverage,
        "all_object_copies_are_elf64_et_rel_x86_64": all_elf_valid and not invalid_objects,
        "manifest_hash_coverage_complete": all_manifest_checked >= sum(EXPECTED.values()) and not all_manifest_mismatch,
        "overall_status": (
            "PASS_STRUCTURE_ELF_AND_MANIFESTS"
            if all_coverage and all_elf_valid and not invalid_objects
               and not unreadable_archives and not duplicate_archive_names
               and all_manifest_checked >= sum(EXPECTED.values()) and not all_manifest_mismatch
            else "PASS_STRUCTURE_ELF_MANIFESTS_INCOMPLETE"
            if all_coverage and all_elf_valid and not invalid_objects
               and not unreadable_archives and not duplicate_archive_names
            else "FAIL_OR_INCOMPLETE"
        ),
        "private_source_contents_exported": False,
        "inputs_modified": False,
        "files_extracted": False,
        "compilation_performed": False,
        "link_performed": False,
        "eboot_created": False,
        "pkg_created": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only audit of private Castlevania AOT object backups")
    parser.add_argument("--root", type=Path, required=True, help="Folder containing private backups/archives")
    parser.add_argument("--report", type=Path, help="Optional JSON report path OUTSIDE --root")
    args = parser.parse_args()
    try:
        result = audit(args.root)
        payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.report:
            destination = safe_report_destination(args.root, args.report)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(payload, encoding="utf-8")
        print(payload)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(json.dumps({"overall_status":"ERROR","error":type(exc).__name__,"message":str(exc)[:300]},ensure_ascii=False))
        return 2
    return 0 if result["overall_status"] == "PASS_STRUCTURE_ELF_AND_MANIFESTS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
