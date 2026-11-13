#!/usr/bin/env python3
"""Private, read-only ELF64 AOT symbol inventory for Etapa 91.

Reads loose ELF objects and ZIP/TAR.GZ members one at a time. It never writes
extracted objects, compiles, links, uploads, or changes the input tree.
The optional JSON report contains mangled symbol names and MUST stay private.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import io
import json
from pathlib import Path, PurePosixPath
import re
import struct
import sys
import tarfile
import zipfile

# Allow both direct script execution and unittest invocation from tests/.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.etapa90.audit_private_aot_objects import EXPECTED, OBJECT, module_for

ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
SECTION = struct.Struct("<IIQQQQIIQQ")
SYMBOL = struct.Struct("<IBBHQQ")
SHT_SYMTAB = 2
SHT_DYNSYM = 11
SHT_GROUP = 17
GRP_COMDAT = 1
SHN_UNDEF = 0
GLOBAL_BINDINGS = {1: "GLOBAL", 2: "WEAK", 10: "GNU_UNIQUE"}
SYMBOL_TYPES = {
    0: "NOTYPE", 1: "OBJECT", 2: "FUNC", 3: "SECTION", 4: "FILE",
    5: "COMMON", 6: "TLS", 10: "GNU_IFUNC",
}
SYMBOL_VISIBILITIES = {0: "DEFAULT", 1: "INTERNAL", 2: "HIDDEN", 3: "PROTECTED"}


def parse_elf_symbols(blob: bytes) -> dict:
    """Return global symbol names and detailed metadata for ELF64 LE x86-64."""
    if len(blob) < ELF_HEADER.size:
        raise ValueError("truncated_elf_header")
    header = ELF_HEADER.unpack_from(blob)
    ident = header[0]
    if ident[:4] != b"\x7fELF" or ident[4] != 2 or ident[5] != 1 or ident[6] != 1:
        raise ValueError("not_elf64_little_endian")
    e_type, e_machine = header[1], header[2]
    if e_type != 1 or e_machine != 62:
        raise ValueError("not_elf64_et_rel_x86_64")
    shoff, shentsize, shnum = header[6], header[11], header[12]
    if shentsize != SECTION.size or shnum == 0:
        raise ValueError("unsupported_or_missing_section_table")
    if shoff > len(blob) or shnum > (len(blob) - shoff) // shentsize:
        raise ValueError("section_table_out_of_bounds")

    sections = [SECTION.unpack_from(blob, shoff + i * shentsize) for i in range(shnum)]
    comdat_sections_by_symtab: dict[int, set[int]] = defaultdict(set)
    for group in sections:
        if group[1] != SHT_GROUP:
            continue
        group_offset, group_size, symtab_index = group[4], group[5], group[6]
        if symtab_index >= len(sections) or sections[symtab_index][1] not in (SHT_SYMTAB, SHT_DYNSYM):
            raise ValueError("invalid_comdat_symbol_table_link")
        if group_size < 4 or group_size % 4:
            raise ValueError("invalid_section_group_size")
        if group_offset > len(blob) or group_size > len(blob) - group_offset:
            raise ValueError("section_group_out_of_bounds")
        words = struct.unpack_from("<" + "I" * (group_size // 4), blob, group_offset)
        if words[0] & GRP_COMDAT:
            for member_index in words[1:]:
                if member_index >= len(sections):
                    raise ValueError("section_group_member_out_of_bounds")
                comdat_sections_by_symtab[symtab_index].add(member_index)

    defined: dict[str, set[str]] = defaultdict(set)
    undefined: dict[str, set[str]] = defaultdict(set)
    defined_details: dict[str, list[dict]] = defaultdict(list)
    symbol_count = 0

    for section_index, sec in enumerate(sections):
        sh_type, sh_offset, sh_size, sh_link, sh_entsize = sec[1], sec[4], sec[5], sec[6], sec[9]
        if sh_type not in (SHT_SYMTAB, SHT_DYNSYM):
            continue
        if sh_entsize != SYMBOL.size or sh_size % sh_entsize:
            raise ValueError("invalid_symbol_table_entry_size")
        if sh_link >= len(sections):
            raise ValueError("symbol_string_table_link_out_of_bounds")
        if sh_offset > len(blob) or sh_size > len(blob) - sh_offset:
            raise ValueError("symbol_table_out_of_bounds")
        strings_sec = sections[sh_link]
        str_offset, str_size = strings_sec[4], strings_sec[5]
        if str_offset > len(blob) or str_size > len(blob) - str_offset:
            raise ValueError("string_table_out_of_bounds")
        strings = blob[str_offset:str_offset + str_size]
        comdat_sections = comdat_sections_by_symtab.get(section_index, set())
        for pos in range(sh_offset, sh_offset + sh_size, sh_entsize):
            st_name, st_info, st_other, st_shndx, _st_value, _st_size = SYMBOL.unpack_from(blob, pos)
            binding = st_info >> 4
            symbol_type = st_info & 0x0F
            visibility = st_other & 0x03
            if binding not in GLOBAL_BINDINGS or st_name == 0:
                continue
            if st_name >= len(strings):
                raise ValueError("symbol_name_offset_out_of_bounds")
            end = strings.find(b"\0", st_name)
            if end < 0:
                raise ValueError("unterminated_symbol_name")
            name = strings[st_name:end].decode("utf-8", "surrogateescape")
            if not name:
                continue
            symbol_count += 1
            binding_name = GLOBAL_BINDINGS[binding]
            if st_shndx == SHN_UNDEF:
                undefined[name].add(binding_name)
            else:
                defined[name].add(binding_name)
                defined_details[name].append({
                    "binding": binding_name,
                    "type": SYMBOL_TYPES.get(symbol_type, f"OTHER_{symbol_type}"),
                    "visibility": SYMBOL_VISIBILITIES.get(visibility, f"OTHER_{visibility}"),
                    "section_index": st_shndx,
                    "comdat": st_shndx in comdat_sections,
                })

    return {
        "defined": {k: sorted(v) for k, v in sorted(defined.items())},
        "undefined": {k: sorted(v) for k, v in sorted(undefined.items())},
        "defined_details": {k: v for k, v in sorted(defined_details.items())},
        "external_symbol_entries": symbol_count,
    }

def classify(name: str) -> str:
    if name.startswith(("nx::", "_ZN2nx", "_ZN3nx")):
        return "nx_runtime"
    if name.startswith(("plat::", "_ZN4plat")):
        return "platform"
    if name.startswith(("__cxa_", "__gxx_", "_Unwind_", "_Z", "std::")):
        return "cxx_abi"
    if name in {"ceil", "floor", "fma", "trunc", "sqrt", "sin", "cos", "pow"}:
        return "libm"
    return "c_or_other"


def build_provider_candidates(all_definitions: dict[str, list[str]], all_undefined: dict[str, set[str]]) -> dict:
    """Map each consuming object location to definitions in other AOT objects."""
    candidates = {}
    for name, consumers in all_undefined.items():
        definitions = sorted(set(all_definitions.get(name, [])))
        by_consumer = {}
        for consumer in sorted(consumers):
            providers = [
                location for location in definitions
                if location != consumer
            ]
            if providers:
                by_consumer[consumer] = providers
        if by_consumer:
            candidates[name] = by_consumer
    return candidates


def summarize_provider_candidates(provider_candidates: dict) -> dict[str, int]:
    """Return aggregate counts for consumer-object/symbol provider candidates."""
    consumer_pairs = 0
    single_provider_pairs = 0
    multiple_provider_pairs = 0
    cross_module_pairs = 0
    max_providers_per_pair = 0

    for consumers in provider_candidates.values():
        for consumer, providers in consumers.items():
            unique_providers = sorted(set(providers))
            if not unique_providers:
                continue
            consumer_pairs += 1
            provider_count = len(unique_providers)
            max_providers_per_pair = max(max_providers_per_pair, provider_count)
            if provider_count == 1:
                single_provider_pairs += 1
            else:
                multiple_provider_pairs += 1
            if any(
                provider.split(":", 1)[0] != consumer.split(":", 1)[0]
                for provider in unique_providers
            ):
                cross_module_pairs += 1

    return {
        "undefined_consumer_object_symbol_pairs_with_aot_provider_candidates": consumer_pairs,
        "undefined_consumer_object_symbol_pairs_with_single_provider_candidate": single_provider_pairs,
        "undefined_consumer_object_symbol_pairs_with_multiple_provider_candidates": multiple_provider_pairs,
        "undefined_consumer_object_symbol_pairs_with_cross_module_provider_candidates": cross_module_pairs,
        "max_aot_provider_candidates_per_consumer_object_symbol_pair": max_providers_per_pair,
    }


def summarize_duplicate_definitions(
    all_definitions: dict[str, list[str]],
    definition_metadata: dict[str, dict[str, list[dict]]],
) -> tuple[dict, dict]:
    """Summarize binding/type/visibility/COMDAT data for multiply-defined symbols."""
    profiles = {}
    binding_totals = Counter()
    type_totals = Counter()
    visibility_totals = Counter()
    duplicate_locations = 0
    comdat_locations = 0
    non_comdat_locations = 0
    names_all_comdat = 0
    names_weak_or_unique_only = 0
    names_non_comdat_global_across_modules = 0

    for name, locations in sorted(all_definitions.items()):
        unique_locations = sorted(set(locations))
        if len(unique_locations) < 2:
            continue

        modules = sorted({loc.split(":", 1)[0] for loc in unique_locations})
        location_profiles = []
        non_comdat_global_modules = set()
        for location in unique_locations:
            entries = definition_metadata.get(name, {}).get(location, [])
            bindings = sorted({item["binding"] for item in entries})
            types = sorted({item["type"] for item in entries})
            visibilities = sorted({item["visibility"] for item in entries})
            section_indexes = sorted({item["section_index"] for item in entries})
            is_comdat = bool(entries) and all(item["comdat"] for item in entries)
            if any(item["binding"] == "GLOBAL" and not item["comdat"] for item in entries):
                non_comdat_global_modules.add(location.split(":", 1)[0])
            for item in entries:
                binding_totals[item["binding"]] += 1
                type_totals[item["type"]] += 1
                visibility_totals[item["visibility"]] += 1
            location_profiles.append({
                "location": location,
                "bindings": bindings,
                "types": types,
                "visibilities": visibilities,
                "section_indexes": section_indexes,
                "comdat": is_comdat,
                "metadata_entries": len(entries),
            })

        all_locations_comdat = bool(location_profiles) and all(x["comdat"] for x in location_profiles)
        only_weak_or_unique = bool(location_profiles) and all(
            x["bindings"] and set(x["bindings"]).issubset({"WEAK", "GNU_UNIQUE"})
            for x in location_profiles
        )
        if all_locations_comdat:
            names_all_comdat += 1
        if only_weak_or_unique:
            names_weak_or_unique_only += 1
        if len(non_comdat_global_modules) > 1:
            names_non_comdat_global_across_modules += 1

        duplicate_locations += len(location_profiles)
        comdat_locations += sum(1 for x in location_profiles if x["comdat"])
        non_comdat_locations += sum(1 for x in location_profiles if not x["comdat"])
        profiles[name] = {
            "location_count": len(unique_locations),
            "module_names": modules,
            "all_locations_comdat": all_locations_comdat,
            "only_weak_or_gnu_unique_bindings": only_weak_or_unique,
            "non_comdat_global_modules": sorted(non_comdat_global_modules),
            "locations": location_profiles,
        }

    totals = {
        "duplicate_definition_symbol_names": len(profiles),
        "duplicate_definition_locations": duplicate_locations,
        "duplicate_definition_locations_with_comdat": comdat_locations,
        "duplicate_definition_locations_without_comdat": non_comdat_locations,
        "duplicate_definition_symbol_names_all_locations_comdat": names_all_comdat,
        "duplicate_definition_symbol_names_only_weak_or_gnu_unique": names_weak_or_unique_only,
        "duplicate_definition_symbol_names_with_non_comdat_global_in_multiple_modules": names_non_comdat_global_across_modules,
        "duplicate_definition_binding_entry_counts": dict(sorted(binding_totals.items())),
        "duplicate_definition_type_entry_counts": dict(sorted(type_totals.items())),
        "duplicate_definition_visibility_entry_counts": dict(sorted(visibility_totals.items())),
    }
    return profiles, totals


def audit(root: Path) -> dict:
    root = root.expanduser()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("--root must be a real directory, not a symlink")
    objects: dict[str, dict[int, list[dict]]] = {m: {} for m in EXPECTED}
    invalid = []
    archive_counts = Counter()
    members_seen = 0
    loose_seen = 0

    def consume(module: str | None, name: str, data: bytes, source: str) -> None:
        match = OBJECT.fullmatch(PurePosixPath(name).name)
        if not match or module not in EXPECTED:
            return
        index = int(match.group(1))
        try:
            symbols = parse_elf_symbols(data)
        except ValueError as exc:
            invalid.append({"module": module, "index": index, "source": source, "reason": str(exc)})
            return
        objects[module].setdefault(index, []).append({
            "index": index, "source": source, **symbols
        })

    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if zipfile.is_zipfile(path):
            archive_counts["ZIP"] += 1
            try:
                with zipfile.ZipFile(path) as zf:
                    for info in zf.infolist():
                        if info.is_dir():
                            continue
                        members_seen += 1
                        inner = info.filename.replace("\\", "/")
                        module = module_for(tuple(PurePosixPath(inner).parts)) or module_for(tuple(Path(rel).parts))
                        if OBJECT.fullmatch(PurePosixPath(inner).name) and module:
                            consume(module, inner, zf.read(info), f"{rel}::{inner}")
            except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                invalid.append({"source": rel, "reason": f"zip_read:{type(exc).__name__}"})
            continue
        try:
            with path.open("rb") as f:
                magic = f.read(2)
            if magic == b"\x1f\x8b" and path.name.lower().endswith((".tar.gz", ".tgz")):
                archive_counts["TAR_GZ"] += 1
                with tarfile.open(path, mode="r:gz") as tf:
                    for info in tf:
                        if not info.isfile():
                            continue
                        members_seen += 1
                        inner = info.name.replace("\\", "/")
                        module = module_for(tuple(PurePosixPath(inner).parts)) or module_for(tuple(Path(rel).parts))
                        if OBJECT.fullmatch(PurePosixPath(inner).name) and module:
                            stream = tf.extractfile(info)
                            if stream is None:
                                invalid.append({"source": f"{rel}::{inner}", "reason": "tar_member_unreadable"})
                            else:
                                with stream:
                                    consume(module, inner, stream.read(), f"{rel}::{inner}")
                continue
        except (OSError, EOFError, tarfile.TarError, gzip.BadGzipFile) as exc:
            invalid.append({"source": rel, "reason": f"archive_read:{type(exc).__name__}"})
            continue

        loose_seen += 1
        module = module_for(tuple(Path(rel).parts))
        if OBJECT.fullmatch(path.name) and module:
            try:
                consume(module, path.name, path.read_bytes(), rel)
            except OSError as exc:
                invalid.append({"source": rel, "reason": f"file_read:{type(exc).__name__}"})

    module_results = {}
    all_definitions: dict[str, list[str]] = defaultdict(list)
    all_undefined: dict[str, set[str]] = defaultdict(set)
    all_definition_metadata: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    total_objects = 0
    for module, expected in EXPECTED.items():
        indices = objects[module]
        defined = Counter()
        undefined = Counter()
        missing = sorted(set(range(expected)) - set(indices))
        unexpected = sorted(i for i in indices if i < 0 or i >= expected)
        for index, copies in indices.items():
            for copy in copies:
                total_objects += 1
                for name, bindings in copy["defined"].items():
                    defined[name] += 1
                    all_definitions[name].append(f"{module}:{index}")
                for name in copy["undefined"]:
                    undefined[name] += 1
                    all_undefined[name].add(f"{module}:{index}")
        module_results[module] = {
            "expected_indices": expected,
            "indices_found": len(indices),
            "object_copies_parsed": sum(len(v) for v in indices.values()),
            "missing_indices": missing,
            "unexpected_indices": unexpected,
            "unique_defined_symbols": len(defined),
            "unique_undefined_symbols": len(undefined),
            "multiply_defined_symbols_within_module": sorted(k for k, v in defined.items() if v > 1),
        }

    cross_module_candidates = {
        name: sorted(set(locations))
        for name, locations in all_definitions.items()
        if len({item.split(":", 1)[0] for item in locations}) > 1
    }
    unresolved_in_inventory = {
        name: sorted(modules)
        for name, modules in all_undefined.items()
        if name not in all_definitions
    }
    provider_candidates = build_provider_candidates(all_definitions, all_undefined)
    provider_candidate_stats = summarize_provider_candidates(provider_candidates)
    duplicate_definition_profiles, duplicate_definition_stats = summarize_duplicate_definitions(
        all_definitions, all_definition_metadata
    )
    cross_module_provider_names = {
        name for name, consumers in provider_candidates.items()
        if any(
            provider.split(":", 1)[0] != consumer.split(":", 1)[0]
            for consumer, providers in consumers.items()
            for provider in providers
        )
    }
    return {
        "audit_mode": "READ_ONLY_SYMBOL_TABLE_PARSE_NO_EXTRACT_NO_COMPILE_NO_LINK",
        "root_name": root.name,
        "archive_format_counts": dict(archive_counts),
        "archive_members_enumerated": members_seen,
        "loose_files_enumerated": loose_seen,
        "module_results": module_results,
        "totals": {
            "expected_object_indices": sum(EXPECTED.values()),
            "object_copies_parsed": total_objects,
            "unique_defined_symbols": len(all_definitions),
            "unique_undefined_symbols": len(all_undefined),
            "symbols_with_definitions_in_multiple_modules": len(cross_module_candidates),
            "undefined_symbols_without_provider_in_aot_inventory": len(unresolved_in_inventory),
            "undefined_symbols_with_aot_provider_candidates": len(provider_candidates),
            "undefined_symbols_with_cross_module_provider_candidates": len(cross_module_provider_names),
            **provider_candidate_stats,
            **duplicate_definition_stats,
        },
        "cross_module_definition_candidates": cross_module_candidates,
        "duplicate_definition_profiles": duplicate_definition_profiles,
        "undefined_symbol_provider_candidates": provider_candidates,
        "undefined_without_aot_provider": unresolved_in_inventory,
        "invalid_objects": invalid,
        "index_coverage_complete": all(not x["missing_indices"] and not x["unexpected_indices"] for x in module_results.values()),
        "private_symbol_names_in_report": True,
        "inputs_modified": False,
        "files_extracted": False,
        "compilation_performed": False,
        "link_performed": False,
        "eboot_created": False,
        "pkg_created": False,
        "limitations": [
            "A matching symbol name is only a candidate, not proof of ABI compatibility.",
            "This inventory does not evaluate relocations, symbol versions, calling conventions, or transitive library dependencies.",
            "The report contains private mangled symbol names and must not be uploaded or committed."
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Private read-only AOT ELF symbol inventory")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True, help="Private JSON path outside the audited tree")
    args = parser.parse_args()
    result = audit(args.root)
    report = json.dumps(result, ensure_ascii=True, indent=2) + "\n"
    destination = args.report.expanduser().absolute()
    root = args.root.expanduser().resolve()
    if destination.is_symlink() or destination.parent.resolve() == root or root in destination.parent.resolve().parents:
        parser.error("--report must be outside the private input tree and not a symlink")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report, encoding="utf-8")
    print(json.dumps({
        "status": "SYMBOL_INVENTORY_COMPLETE" if not result["invalid_objects"] else "SYMBOL_INVENTORY_WITH_ERRORS",
        "modules": {k: {"indices_found": v["indices_found"], "unique_defined_symbols": v["unique_defined_symbols"], "unique_undefined_symbols": v["unique_undefined_symbols"]} for k, v in result["module_results"].items()},
        "totals": result["totals"],
        "report_path": str(destination),
        "private_symbol_names_written_to_report": True,
    }, ensure_ascii=True, indent=2))
    return 0 if not result["invalid_objects"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
