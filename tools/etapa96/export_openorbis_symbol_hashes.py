#!/usr/bin/env python3
"""Export a name-free SHA-256 inventory of OpenOrbis v0.5.4 global definitions."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import shutil
import subprocess
import sys
import tarfile
from collections import Counter
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.etapa90.private_aot_sdk_provider_audit import (  # noqa: E402
    _archive_member_suffix,
    _has_symlink_component,
    parse_nm_records,
)

SDK_RELEASE = "v0.5.4"
SDK_SHA256 = "3c7cd5bb593ca74fa1c13fd59f3938dc0fc07985167f7275063019e63abe4526"
TARGET_TRIPLE = "x86_64-pc-freebsd12-elf"
SUFFIXES = {".a", ".so", ".o", ".elf", ".prx"}


class AuditError(Exception):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_provider_name(name: str) -> bool:
    lower = name.lower()
    return (
        Path(lower).suffix in SUFFIXES
        or lower.endswith(".so")
        or (
            ".so." in lower
            and lower.rsplit(".so.", 1)[1]
            and all(part.isdigit() for part in lower.rsplit(".so.", 1)[1].split("."))
        )
    )


def _lib_member_path(name: str):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise AuditError("SDK_ARCHIVE_UNSAFE_PATH")
    parts = tuple(part for part in path.parts if part not in ("", "."))
    if not parts or parts[0] != "lib":
        return None
    return PurePosixPath(*parts[1:])


def _link_target(member_name: str, link_name: str, hardlink: bool) -> PurePosixPath:
    link = PurePosixPath(link_name)
    if link.is_absolute() or "\x00" in link_name:
        raise AuditError("SDK_LIB_LINK_UNSAFE")
    member = PurePosixPath(member_name)
    combined = link if hardlink else PurePosixPath(*member.parts[:-1], *link.parts)
    normalized = posixpath.normpath(str(combined))
    target = PurePosixPath(normalized)
    if target.is_absolute() or ".." in target.parts or not target.parts or target.parts[0] != "lib":
        raise AuditError("SDK_LIB_LINK_ESCAPES_ROOT")
    return PurePosixPath(*target.parts[1:])


def extract_openorbis_lib(archive: Path, destination: Path) -> int:
    archive = Path(archive).absolute()
    destination = Path(destination).absolute()
    if _has_symlink_component(archive) or not archive.is_file():
        raise AuditError("SDK_ARCHIVE_NOT_REGULAR")
    if _has_symlink_component(destination) or destination.is_symlink():
        raise AuditError("SDK_DESTINATION_NOT_SAFE")
    if destination.exists() and any(destination.iterdir()):
        raise AuditError("SDK_DESTINATION_NOT_EMPTY")
    if sha256_file(archive) != SDK_SHA256:
        raise AuditError("SDK_ARCHIVE_SHA256_MISMATCH")

    destination.mkdir(parents=True, exist_ok=True)
    regular = []
    directories = []
    links = []
    seen = set()

    try:
        with tarfile.open(archive, "r:gz") as bundle:
            for member in bundle.getmembers():
                rel = _lib_member_path(member.name)
                if rel is None or not rel.parts:
                    continue
                key = rel.as_posix()
                if key in seen:
                    raise AuditError("SDK_LIB_DUPLICATE_MEMBER")
                seen.add(key)
                target = destination.joinpath(*rel.parts)
                if member.isdir():
                    directories.append((target, member.mode))
                elif member.isfile():
                    regular.append((member, target))
                elif member.issym() or member.islnk():
                    links.append((member, target, _link_target(member.name, member.linkname, member.islnk())))
                else:
                    raise AuditError("SDK_LIB_SPECIAL_FILE")

            for target, mode in sorted(directories, key=lambda row: len(row[0].parts)):
                target.mkdir(parents=True, exist_ok=True)
            count = 0
            for member, target in regular:
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists() or target.is_symlink():
                    raise AuditError("SDK_LIB_PATH_COLLISION")
                source = bundle.extractfile(member)
                if source is None:
                    raise AuditError("SDK_LIB_MEMBER_UNREADABLE")
                with source, target.open("xb") as output:
                    shutil.copyfileobj(source, output, 1024 * 1024)
                count += 1

            pending = list(links)
            while pending:
                deferred = []
                progress = False
                for member, alias, target_rel in pending:
                    target = destination.joinpath(*target_rel.parts)
                    try:
                        resolved = target.resolve(strict=True)
                    except FileNotFoundError:
                        deferred.append((member, alias, target_rel))
                        continue
                    root_real = destination.resolve(strict=True)
                    if not resolved.is_relative_to(root_real):
                        raise AuditError("SDK_LIB_LINK_ESCAPES_ROOT")
                    if not (resolved.is_file() or resolved.is_dir()):
                        raise AuditError("SDK_LIB_LINK_TARGET_INVALID")
                    alias.parent.mkdir(parents=True, exist_ok=True)
                    if alias.exists() or alias.is_symlink():
                        raise AuditError("SDK_LIB_PATH_COLLISION")
                    os.symlink(os.path.relpath(resolved, alias.parent), alias)
                    progress = True
                if not progress and deferred:
                    raise AuditError("SDK_LIB_LINK_TARGET_MISSING")
                pending = deferred
    except (tarfile.TarError, OSError):
        raise AuditError("SDK_ARCHIVE_EXTRACTION_FAILED") from None

    if count == 0:
        raise AuditError("SDK_LIB_EMPTY")
    return count


def collect_provider_files(root: Path):
    root = Path(root).absolute()
    if _has_symlink_component(root) or not root.is_dir():
        raise AuditError("SDK_LIB_ROOT_NOT_SAFE")
    root_real = root.resolve(strict=True)
    visited_dirs = set()
    files = {}
    symlink_aliases = 0

    def visit(directory: Path):
        nonlocal symlink_aliases
        real_dir = directory.resolve(strict=True)
        if not real_dir.is_relative_to(root_real):
            raise AuditError("SDK_LIB_SYMLINK_ESCAPES_ROOT")
        if real_dir in visited_dirs:
            return
        if not real_dir.is_dir():
            raise AuditError("SDK_LIB_DIRECTORY_INVALID")
        visited_dirs.add(real_dir)
        for child in sorted(real_dir.iterdir(), key=lambda item: item.name):
            if child.is_symlink():
                symlink_aliases += 1
                try:
                    target = child.resolve(strict=True)
                except OSError:
                    raise AuditError("SDK_LIB_SYMLINK_BROKEN") from None
                if not target.is_relative_to(root_real):
                    raise AuditError("SDK_LIB_SYMLINK_ESCAPES_ROOT")
                if target.is_dir():
                    visit(target)
                elif target.is_file():
                    if is_provider_name(child.name) or is_provider_name(target.name):
                        files[target] = target
                else:
                    if is_provider_name(child.name):
                        raise AuditError("SDK_LIB_SYMLINK_TARGET_INVALID")
            elif child.is_dir():
                visit(child)
            elif child.is_file():
                if is_provider_name(child.name):
                    real = child.resolve(strict=True)
                    if not real.is_relative_to(root_real):
                        raise AuditError("SDK_LIB_FILE_ESCAPES_ROOT")
                    files[real] = real
            elif is_provider_name(child.name):
                raise AuditError("SDK_LIB_SPECIAL_PROVIDER")

    visit(root_real)
    return sorted(files.values(), key=lambda item: item.relative_to(root_real).as_posix()), symlink_aliases


def build_symbol_hash_manifest(root: Path, nm: str, archive_sha256: str):
    tool = shutil.which(nm)
    if not tool:
        raise AuditError("NM_EXECUTABLE_NOT_FOUND")
    files, symlink_aliases = collect_provider_files(root)
    if not files:
        raise AuditError("SDK_LIB_NO_PROVIDER_FILES")

    counts = Counter()
    kinds = {}
    identities = set()
    entries = 0
    for path in files:
        try:
            process = subprocess.run(
                [tool, "-A", "-g", "--defined-only", "--format=posix", str(path)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise AuditError("NM_EXECUTION_FAILED") from None
        if process.returncode != 0 or process.stderr.strip():
            raise AuditError("NM_PROVIDER_SCAN_FAILED")
        try:
            rows = parse_nm_records(process.stdout)
        except ValueError:
            raise AuditError("NM_OUTPUT_UNRECOGNIZED") from None
        for origin, name, kind in rows:
            member = _archive_member_suffix(origin, path)
            identity = (str(path.resolve()), member, name, kind)
            if identity in identities:
                continue
            identities.add(identity)
            digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
            counts[digest] += 1
            kinds.setdefault(digest, set()).add(kind)
            entries += 1

    if not counts:
        raise AuditError("SDK_LIB_NO_DEFINED_GLOBAL_SYMBOLS")

    symbol_hashes = [
        {
            "sha256": digest,
            "definition_count": counts[digest],
            "kinds": sorted(kinds[digest]),
        }
        for digest in sorted(counts)
    ]
    canonical = "".join(
        f"{row['sha256']}:{row['definition_count']}:{','.join(row['kinds'])}\n"
        for row in symbol_hashes
    )
    return {
        "schema_version": 1,
        "provider_scope": "OPENORBIS_V054_LIB_ONLY",
        "sdk_release": SDK_RELEASE,
        "sdk_archive_sha256": archive_sha256,
        "target_triple": TARGET_TRIPLE,
        "provider_file_count": len(files),
        "provider_symlink_aliases_resolved": symlink_aliases,
        "defined_nm_entries_seen": entries,
        "unique_provider_definitions_seen": len(identities),
        "unique_symbol_hash_count": len(symbol_hashes),
        "symbol_hashes": symbol_hashes,
        "symbol_hash_manifest_sha256": hashlib.sha256(canonical.encode("ascii")).hexdigest(),
        "hash_algorithm": "SHA-256 of exact UTF-8 symbol name",
        "symbol_names_included": False,
        "provider_paths_included": False,
        "private_aot_data_included": False,
        "scan_complete": True,
        "abi_compatibility_proven": False,
        "limitations": [
            "Exact-name hash matches are provider candidates only.",
            "No symbol-version, relocation, calling-convention, type-layout, or transitive-dependency validation.",
            "Only OpenOrbis v0.5.4 lib/ was scanned; PS4 runtime objects remain a separate provider root.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--extract-root", type=Path, required=True)
    parser.add_argument("--nm", default="nm")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        actual_sha = sha256_file(args.archive)
        if actual_sha != SDK_SHA256:
            raise AuditError("SDK_ARCHIVE_SHA256_MISMATCH")
        extract_openorbis_lib(args.archive, args.extract_root)
        report = build_symbol_hash_manifest(args.extract_root, args.nm, actual_sha)
        output = args.output.absolute()
        if _has_symlink_component(output.parent) or output.is_symlink():
            raise AuditError("OUTPUT_PATH_NOT_SAFE")
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = output.with_name(output.name + ".tmp")
        temp.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        os.replace(temp, output)
        print(
            "OPENORBIS_SYMBOL_HASH_EXPORT=PASS "
            f"FILES={report['provider_file_count']} "
            f"DEFINITIONS={report['defined_nm_entries_seen']} "
            f"UNIQUE_HASHES={report['unique_symbol_hash_count']} "
            f"SAFE_SYMLINK_ALIASES={report['provider_symlink_aliases_resolved']}"
        )
        print(f"SYMBOL_HASH_MANIFEST_SHA256={report['symbol_hash_manifest_sha256']}")
        return 0
    except (AuditError, OSError, ValueError, tarfile.TarError, subprocess.TimeoutExpired) as error:
        code = str(error) if isinstance(error, AuditError) else type(error).__name__
        print("OPENORBIS_SYMBOL_HASH_EXPORT=FAILED:" + code, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
