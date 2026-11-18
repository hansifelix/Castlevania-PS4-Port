#!/usr/bin/env python3
"""Export a name-free provider manifest from the pinned public PS4 runtime objects.

The input objects are compiled from public upstream source for the OpenOrbis PS4
target. This tool records only SHA-256 hashes of exact UTF-8 symbol names,
counts, and type letters. It never writes symbol names, object paths, or object
bytes to the manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

NM_ROW = re.compile(
    r"^(?P<origin>.*?):\s+(?P<symbol>\S+)\s+(?P<kind>[A-Za-z?])(?:\s+\S+){0,2}$"
)

SDK_RELEASE = "v0.5.4"
SDK_ARCHIVE_SHA256 = "3c7cd5bb593ca74fa1c13fd59f3938dc0fc07985167f7275063019e63abe4526"
RUNTIME_REPOSITORY = "SwonDev/cstlvnia-blmont-to-macos"
RUNTIME_COMMIT = "4043f21bb4f656d34cd17ba070238c7728d00631"
VULKAN_HEADERS_REPOSITORY = "KhronosGroup/Vulkan-Headers"
VULKAN_HEADERS_COMMIT = "acbb9391c0a597272800cd3f4363661c00a27c77"
TARGET_TRIPLE = "x86_64-pc-freebsd12-elf"
EXPECTED_RUNTIME_OBJECTS = 87
EXPECTED_GAME_OBJECTS = 1
EXPECTED_PLATFORM_OBJECTS = 14


class AuditError(Exception):
    pass


def has_symlink_component(path: Path) -> bool:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            return True
    return False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_object_root(
    root: Path,
    expected_runtime=EXPECTED_RUNTIME_OBJECTS,
    expected_game=EXPECTED_GAME_OBJECTS,
    expected_platform=EXPECTED_PLATFORM_OBJECTS,
):
    root = Path(root).absolute()
    if has_symlink_component(root) or not root.is_dir():
        raise AuditError("OBJECT_ROOT_NOT_SAFE_DIRECTORY")
    children = sorted(root.iterdir(), key=lambda item: item.name)
    if any(child.is_symlink() for child in children):
        raise AuditError("OBJECT_ROOT_CONTAINS_SYMLINK")
    if any(not child.is_file() or child.suffix != ".o" for child in children):
        raise AuditError("OBJECT_ROOT_MUST_CONTAIN_ONLY_FLAT_OBJECT_FILES")

    objects = [child for child in children if child.suffix == ".o"]
    runtime = [p for p in objects if p.name.startswith("RT-")]
    game = [p for p in objects if p.name.startswith("GAME-")]
    platform = [p for p in objects if p.name.startswith("PS4-")]
    if len(runtime) != expected_runtime:
        raise AuditError("RUNTIME_OBJECT_COUNT_MISMATCH")
    if len(game) != expected_game:
        raise AuditError("GAME_METADATA_OBJECT_COUNT_MISMATCH")
    if len(platform) != expected_platform:
        raise AuditError("PS4_PLATFORM_OBJECT_COUNT_MISMATCH")
    if len(objects) != expected_runtime + expected_game + expected_platform:
        raise AuditError("UNEXPECTED_OBJECT_FILE")
    if any(path.stat().st_size <= 0 for path in objects):
        raise AuditError("EMPTY_OBJECT_FILE")
    return objects, runtime, game, platform


def parse_nm_records(text: str):
    rows = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == "no symbols" or line.endswith(": no symbols"):
            continue
        match = NM_ROW.match(line)
        if not match:
            raise AuditError("NM_OUTPUT_UNRECOGNIZED")
        name = match.group("symbol")
        kind = match.group("kind")
        if not name or "\x00" in name or kind.upper() == "U":
            raise AuditError("NM_DEFINED_RECORD_INVALID")
        rows.append((name, kind))
    return rows


def build_manifest(
    object_root: Path,
    nm: str = "llvm-nm-18",
    runner=subprocess.run,
    expected_runtime=EXPECTED_RUNTIME_OBJECTS,
    expected_game=EXPECTED_GAME_OBJECTS,
    expected_platform=EXPECTED_PLATFORM_OBJECTS,
):
    tool = shutil.which(nm)
    if not tool:
        raise AuditError("NM_EXECUTABLE_NOT_FOUND")
    objects, runtime, game, platform = inspect_object_root(
        object_root, expected_runtime, expected_game, expected_platform
    )

    counts = Counter()
    kinds = defaultdict(set)
    object_sets = defaultdict(set)
    identities = set()
    entries_seen = 0
    object_rows = []

    for path in objects:
        try:
            process = runner(
                [tool, "-A", "-g", "--defined-only", "--format=posix", str(path)],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise AuditError("NM_EXECUTION_FAILED") from None
        if process.returncode != 0 or process.stderr.strip():
            raise AuditError("NM_PROVIDER_SCAN_FAILED")
        records = parse_nm_records(process.stdout)
        object_class = (
            "runtime" if path.name.startswith("RT-")
            else "game_metadata" if path.name.startswith("GAME-")
            else "ps4_platform"
        )
        object_digest = sha256_file(path)
        object_rows.append((object_class, path.stat().st_size, object_digest))

        for name, kind in records:
            entries_seen += 1
            digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
            identity = (path.name, name, kind)
            if identity in identities:
                continue
            identities.add(identity)
            counts[digest] += 1
            kinds[digest].add(kind)
            object_sets[digest].add(path.name)

    if not counts:
        raise AuditError("NO_GLOBAL_DEFINITIONS_FOUND")

    symbol_hashes = [
        {
            "sha256": digest,
            "definition_count": counts[digest],
            "object_count": len(object_sets[digest]),
            "kinds": sorted(kinds[digest]),
        }
        for digest in sorted(counts)
    ]
    canonical_symbols = "".join(
        f"{row['sha256']}:{row['definition_count']}:{row['object_count']}:{','.join(row['kinds'])}\n"
        for row in symbol_hashes
    )
    canonical_objects = "".join(
        f"{kind}:{size}:{digest}\n"
        for kind, size, digest in sorted(object_rows)
    )
    return {
        "schema_version": 1,
        "provider_scope": "PINNED_PUBLIC_RUNTIME_87_GAME_METADATA_1_PS4_PLATFORM_14",
        "runtime_repository": RUNTIME_REPOSITORY,
        "runtime_commit": RUNTIME_COMMIT,
        "runtime_translation_units": len(runtime),
        "game_metadata_translation_units": len(game),
        "ps4_platform_adapter_units": len(platform),
        "object_count": len(objects),
        "object_bytes_total": sum(path.stat().st_size for path in objects),
        "object_set_sha256": hashlib.sha256(canonical_objects.encode("ascii")).hexdigest(),
        "sdk_release": SDK_RELEASE,
        "sdk_archive_sha256": SDK_ARCHIVE_SHA256,
        "vulkan_headers_repository": VULKAN_HEADERS_REPOSITORY,
        "vulkan_headers_commit": VULKAN_HEADERS_COMMIT,
        "compiler": "clang++-18",
        "target_triple": TARGET_TRIPLE,
        "defined_nm_entries_seen": entries_seen,
        "unique_provider_definitions_seen": len(identities),
        "unique_symbol_hash_count": len(symbol_hashes),
        "symbol_hashes": symbol_hashes,
        "symbol_hash_manifest_sha256": hashlib.sha256(canonical_symbols.encode("ascii")).hexdigest(),
        "hash_algorithm": "SHA-256 of exact UTF-8 symbol name",
        "symbol_names_included": False,
        "provider_paths_included": False,
        "object_names_included": False,
        "private_aot_data_included": False,
        "scan_complete": True,
        "compilation_performed": True,
        "link_performed": False,
        "abi_compatibility_proven": False,
        "eboot_created": False,
        "pkg_created": False,
        "ps4_tested": False,
        "limitations": [
            "Exact-name hash matches are provider candidates only.",
            "No symbol-version, relocation, calling-convention, type-layout, or transitive-dependency validation.",
            "The manifest contains public runtime and platform object definitions only; it does not include private AOT objects.",
            "The objects were compiled but not linked into an executable and were not run on PS4 hardware.",
        ],
    }


def write_manifest(path: Path, manifest: dict, protected_root: Path) -> Path:
    destination = Path(path).expanduser().absolute()
    root = Path(protected_root).resolve(strict=True)
    if has_symlink_component(destination.parent) or destination.is_symlink():
        raise AuditError("OUTPUT_PATH_NOT_SAFE")
    parent = destination.parent.resolve()
    if parent == root or root in parent.parents:
        raise AuditError("OUTPUT_MUST_BE_OUTSIDE_OBJECT_ROOT")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(manifest, stream, ensure_ascii=True, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError:
        raise AuditError("OUTPUT_ALREADY_EXISTS") from None
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--object-root", type=Path, required=True)
    parser.add_argument("--nm", default="llvm-nm-18")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = build_manifest(args.object_root, args.nm)
        destination = write_manifest(args.output, manifest, args.object_root)
    except (OSError, AuditError, subprocess.TimeoutExpired) as exc:
        code = str(exc) if isinstance(exc, AuditError) else type(exc).__name__
        print(f"KAZUMA_ETAPA98_EXPORT=FAILED:{code}", file=sys.stderr)
        return 2
    print(json.dumps({
        "status": "HASH_ONLY_RUNTIME_PROVIDER_MANIFEST_COMPLETE",
        "object_count": manifest["object_count"],
        "runtime_translation_units": manifest["runtime_translation_units"],
        "game_metadata_translation_units": manifest["game_metadata_translation_units"],
        "ps4_platform_adapter_units": manifest["ps4_platform_adapter_units"],
        "defined_nm_entries_seen": manifest["defined_nm_entries_seen"],
        "unique_provider_definitions_seen": manifest["unique_provider_definitions_seen"],
        "unique_symbol_hash_count": manifest["unique_symbol_hash_count"],
        "symbol_hash_manifest_sha256": manifest["symbol_hash_manifest_sha256"],
        "private_names_included": False,
        "provider_paths_included": False,
        "private_aot_data_included": False,
        "abi_compatibility_proven": False,
        "link_performed": False,
        "eboot_created": False,
        "pkg_created": False,
        "ps4_tested": False,
        "report_path": str(destination),
    }, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
