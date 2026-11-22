#!/usr/bin/env python3
"""Private local hash-only join of AOT unresolved names against provider manifests.

This tool reads private AOT symbol names only in memory and emits aggregate
counts. It never writes symbol names, per-symbol hashes, provider paths, or
consumer object identifiers to its report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
INVENTORY_MODE = "READ_ONLY_SYMBOL_TABLE_PARSE_NO_EXTRACT_NO_COMPILE_NO_LINK"


class JoinError(Exception):
    pass


def has_symlink_component(path: Path) -> bool:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            return True
    return False


def load_inventory(path: Path):
    if has_symlink_component(path) or not path.is_file():
        raise JoinError("PRIVATE_INVENTORY_NOT_REGULAR")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise JoinError("PRIVATE_INVENTORY_INVALID") from None
    if (
        data.get("audit_mode") != INVENTORY_MODE
        or data.get("index_coverage_complete") is not True
        or data.get("duplicate_metadata_complete") is not True
        or data.get("invalid_objects") != []
        or data.get("private_symbol_names_in_report") is not True
        or data.get("inputs_modified") is not False
        or data.get("files_extracted") is not False
        or data.get("compilation_performed") is not False
        or data.get("link_performed") is not False
    ):
        raise JoinError("PRIVATE_INVENTORY_NOT_COMPLETE_READ_ONLY")
    totals = data.get("totals")
    pending = data.get("undefined_without_aot_provider")
    if not isinstance(totals, dict) or not isinstance(pending, dict):
        raise JoinError("PRIVATE_INVENTORY_SCHEMA_INVALID")
    if type(totals.get("undefined_symbols_without_provider_in_aot_inventory")) is not int:
        raise JoinError("PRIVATE_INVENTORY_COUNT_INVALID")
    if totals["undefined_symbols_without_provider_in_aot_inventory"] != len(pending):
        raise JoinError("PRIVATE_INVENTORY_COUNT_MISMATCH")
    if any(not isinstance(name, str) or not name for name in pending):
        raise JoinError("PRIVATE_INVENTORY_SYMBOL_KEY_INVALID")
    if any(not isinstance(consumers, list) for consumers in pending.values()):
        raise JoinError("PRIVATE_INVENTORY_CONSUMER_LIST_INVALID")
    return data, pending


def validate_provider_manifest(path: Path):
    if has_symlink_component(path) or not path.is_file():
        raise JoinError("PROVIDER_MANIFEST_NOT_REGULAR")
    try:
        raw = path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise JoinError("PROVIDER_MANIFEST_INVALID") from None
    if (
        data.get("schema_version") != 1
        or data.get("hash_algorithm") != "SHA-256 of exact UTF-8 symbol name"
        or data.get("symbol_names_included") is not False
        or data.get("provider_paths_included") is not False
        or data.get("private_aot_data_included") is not False
        or data.get("scan_complete") is not True
        or data.get("abi_compatibility_proven") is not False
    ):
        raise JoinError("PROVIDER_MANIFEST_NOT_COMPLETE_HASH_ONLY")
    rows = data.get("symbol_hashes")
    if not isinstance(rows, list) or not rows:
        raise JoinError("PROVIDER_MANIFEST_HASH_LIST_INVALID")
    index = {}
    last = ""
    for row in rows:
        if not isinstance(row, dict):
            raise JoinError("PROVIDER_MANIFEST_ROW_INVALID")
        digest = row.get("sha256")
        definitions = row.get("definition_count")
        kinds = row.get("kinds")
        if (
            not isinstance(digest, str) or not SHA256_RE.fullmatch(digest)
            or digest <= last
            or type(definitions) is not int or definitions < 1
            or not isinstance(kinds, list) or not kinds
            or any(not isinstance(kind, str) or len(kind) != 1 for kind in kinds)
            or len(set(kinds)) != len(kinds)
        ):
            raise JoinError("PROVIDER_MANIFEST_ROW_INVALID")
        last = digest
        index[digest] = row
    if data.get("unique_symbol_hash_count") != len(index):
        raise JoinError("PROVIDER_MANIFEST_COUNT_MISMATCH")
    if "object_count" in rows[0]:
        if any(type(row.get("object_count")) is not int or row["object_count"] < 1 for row in rows):
            raise JoinError("PROVIDER_MANIFEST_OBJECT_COUNT_INVALID")
        canonical = "".join(
            f"{row['sha256']}:{row['definition_count']}:{row['object_count']}:{','.join(row['kinds'])}\n"
            for row in rows
        )
    else:
        canonical = "".join(
            f"{row['sha256']}:{row['definition_count']}:{','.join(row['kinds'])}\n"
            for row in rows
        )
    digest = hashlib.sha256(canonical.encode("ascii")).hexdigest()
    if data.get("symbol_hash_manifest_sha256") != digest:
        raise JoinError("PROVIDER_MANIFEST_HASH_MISMATCH")
    return data, index, hashlib.sha256(raw).hexdigest()


def symbol_class(name: str) -> str:
    if name.startswith(("nx::", "_ZN2nx", "_ZN3nx")):
        return "nx_runtime"
    if name.startswith(("plat::", "_ZN4plat")):
        return "platform"
    if name.startswith(("__cxa_", "__gxx_", "_Unwind_", "_Z", "std::")):
        return "cxx_abi"
    if name in {"ceil", "floor", "fma", "trunc", "sqrt", "sin", "cos", "pow", "round", "nearbyint"}:
        return "libm"
    if name.startswith("__atomic_"):
        return "compiler_runtime"
    return "c_or_other"


def module_of_consumer(value: str) -> str:
    module = value.split(":", 1)[0] if isinstance(value, str) else "unknown"
    return module if module in {"main", "sdk", "subsdk0"} else "unknown"


def join_inventory(pending: dict, provider_index: dict, provider_scope: str, manifest_sha256: str):
    matched = 0
    unmatched = 0
    matched_refs = 0
    unmatched_refs = 0
    definition_total = 0
    ambiguous = 0
    single = 0
    by_class = defaultdict(lambda: Counter())
    by_module = defaultdict(lambda: Counter())

    for name, consumers in pending.items():
        digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
        row = provider_index.get(digest)
        category = symbol_class(name)
        ref_count = len(consumers)
        modules = Counter(module_of_consumer(value) for value in consumers)
        if row is None:
            unmatched += 1
            unmatched_refs += ref_count
            by_class[category]["unmatched_symbols"] += 1
            by_class[category]["unmatched_references"] += ref_count
            for module, count in modules.items():
                by_module[module]["unmatched_references"] += count
        else:
            matched += 1
            matched_refs += ref_count
            definitions = row["definition_count"]
            definition_total += definitions
            if definitions > 1:
                ambiguous += 1
            else:
                single += 1
            by_class[category]["matched_symbols"] += 1
            by_class[category]["matched_references"] += ref_count
            for module, count in modules.items():
                by_module[module]["matched_references"] += count

    return {
        "provider_scope": provider_scope,
        "provider_manifest_sha256": manifest_sha256,
        "aot_unresolved_unique_names": len(pending),
        "exact_name_hash_matches": matched,
        "no_provider_hash_match": unmatched,
        "matched_definition_count_total": definition_total,
        "matched_names_with_multiple_definitions": ambiguous,
        "matched_names_with_single_definition": single,
        "matched_consumer_references": matched_refs,
        "unmatched_consumer_references": unmatched_refs,
        "by_symbol_class": {key: dict(value) for key, value in sorted(by_class.items())},
        "by_consumer_module": {key: dict(value) for key, value in sorted(by_module.items())},
    }


def write_report(path: Path, report: dict, protected: list[Path]) -> Path:
    destination = Path(path).expanduser().absolute()
    if has_symlink_component(destination.parent) or destination.is_symlink():
        raise JoinError("REPORT_PATH_NOT_SAFE")
    parent = destination.parent.resolve()
    for source in protected:
        root = source.expanduser().resolve(strict=True)
        if parent == root or root in parent.parents:
            raise JoinError("REPORT_MUST_BE_OUTSIDE_INPUT_ROOTS")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, ensure_ascii=True, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError:
        raise JoinError("REPORT_ALREADY_EXISTS") from None
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--private-root", type=Path, required=True, help="Actual private AOT directory; report must stay outside it.")
    parser.add_argument("--provider-manifest", type=Path, action="append", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        if has_symlink_component(args.private_root) or not args.private_root.is_dir():
            raise JoinError("PRIVATE_ROOT_NOT_SAFE")
        _, pending = load_inventory(args.inventory)
        rows = []
        for path in args.provider_manifest:
            data, index, file_hash = validate_provider_manifest(path)
            rows.append(join_inventory(
                pending, index, str(data.get("provider_scope", "UNKNOWN")), file_hash
            ))
        report = {
            "audit_mode": "PRIVATE_AOT_HASH_ONLY_PROVIDER_JOIN_NO_COMPILE_NO_LINK",
            "provider_results": rows,
            "private_symbol_names_included": False,
            "private_symbol_hashes_included": False,
            "provider_paths_included": False,
            "consumer_object_ids_included": False,
            "aot_inventory_file_hash_included": False,
            "abi_compatibility_proven": False,
            "link_authorized": False,
            "compilation_performed": False,
            "link_performed": False,
            "eboot_created": False,
            "pkg_created": False,
            "ps4_tested": False,
            "limitations": [
                "Exact-name hash matches identify provider candidates only.",
                "The report contains aggregate counts only; it cannot select a provider when definitions are ambiguous.",
                "No symbol-version, relocation, calling-convention, type-layout, or transitive-dependency validation is performed.",
                "A missing match in one manifest does not prove that no provider exists in another root.",
            ],
        }
        destination = write_report(
            args.report, report,
            [args.private_root, *(path.parent for path in args.provider_manifest)]
        )
    except (OSError, JoinError) as exc:
        code = str(exc) if isinstance(exc, JoinError) else type(exc).__name__
        print(f"KAZUMA_PRIVATE_HASH_JOIN=FAILED:{code}")
        return 2
    print(json.dumps({
        "status": "PRIVATE_HASH_JOIN_COMPLETE",
        "provider_manifest_count": len(rows),
        "aot_unresolved_unique_names": len(pending),
        "private_names_included": False,
        "private_hashes_included": False,
        "provider_paths_included": False,
        "abi_compatibility_proven": False,
        "link_performed": False,
        "report_path": str(destination),
    }, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
