#!/usr/bin/env python3
"""Private, read-only exact-name provider scan for private AOT symbols."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

LINE = re.compile(
    r"^(?P<origin>.*?):\\s+(?P<symbol>\\S+)\\s+(?P<kind>[A-Za-z?])(?:\\s+\\S+){0,2}$"
)
VERSIONED_SO = re.compile(r"\\.so(?:\\.\\d+)*$", re.IGNORECASE)
SUFFIXES = {".a", ".so", ".o", ".elf", ".prx"}


def complete(data):
    return (
        data.get("audit_mode") == "READ_ONLY_SYMBOL_TABLE_PARSE_NO_EXTRACT_NO_COMPILE_NO_LINK"
        and data.get("index_coverage_complete") is True
        and data.get("duplicate_metadata_complete") is True
        and not data.get("invalid_objects")
        and data.get("private_symbol_names_in_report") is True
        and data.get("files_extracted") is False
        and data.get("compilation_performed") is False
        and data.get("link_performed") is False
        and isinstance(data.get("undefined_without_aot_provider"), dict)
        and data.get("totals", {}).get("undefined_symbols_without_provider_in_aot_inventory")
        == len(data.get("undefined_without_aot_provider", {}))
    )


def parse_nm_records(text):
    """Return (origin, symbol, kind); origin retains archive-member identity."""
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.endswith(": no symbols") or line == "no symbols":
            continue
        if line.startswith(("warning:", "nm: warning:", "llvm-nm: warning:")):
            raise ValueError("nm_warning_in_output")
        match = LINE.match(line)
        if not match:
            if line.startswith(("nm:", "llvm-nm:")):
                continue
            raise ValueError("unrecognized_nm_posix_line")
        kind = match.group("kind")
        if kind.upper() != "U":
            out.append((match.group("origin"), match.group("symbol"), kind))
    return out


def parse_nm(text):
    """Backward-compatible symbol/kind view used by existing callers."""
    return [(symbol, kind) for _, symbol, kind in parse_nm_records(text)]


def _has_symlink_component(path):
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            return True
    return False


def provider_files(root):
    root = Path(root).absolute()
    if _has_symlink_component(root) or not root.is_dir():
        raise ValueError("provider_root_not_real_directory")

    found = []
    walk_errors = []

    def record_walk_error(error):
        walk_errors.append(error)

    for current, directories, filenames in os.walk(
        root, topdown=True, followlinks=False, onerror=record_walk_error
    ):
        current_path = Path(current)
        directories[:] = sorted(
            name for name in directories
            if not (current_path / name).is_symlink()
        )
        for name in sorted(filenames):
            path = current_path / name
            if path.is_symlink():
                continue
            if path.suffix.lower() in SUFFIXES or VERSIONED_SO.search(path.name):
                if path.is_file():
                    found.append(path)

    if walk_errors:
        raise ValueError("provider_tree_walk_incomplete")
    return found


def _archive_member_suffix(origin, path):
    prefix = str(path)
    if origin.startswith(prefix):
        suffix = origin[len(prefix):]
        return suffix[1:] if suffix.startswith(":") else suffix
    # Some nm implementations print a relative origin. Keep only its basename
    # rather than leaking an unrelated absolute path into the private report.
    return Path(origin).name


def scan(data, roots, nm):
    if not complete(data):
        raise ValueError("inventory_incomplete_or_not_read_only")

    providers = defaultdict(list)
    errors = []
    scanned = 0
    symbols = 0
    unique_definitions = set()
    root_rows = []

    for label, root in roots:
        root = Path(root).absolute()
        files = provider_files(root)
        root_rows.append({"label": label, "library_count": len(files)})
        for path in files:
            scanned += 1
            try:
                process = subprocess.run(
                    [nm, "-A", "-g", "--defined-only", "--format=posix", str(path)],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=300,
                )
                if process.returncode:
                    raise RuntimeError("nm_failed")
                if process.stderr.strip():
                    raise RuntimeError("nm_emitted_stderr")
                rows = parse_nm_records(process.stdout)
                symbols += len(rows)
                for origin, name, kind in rows:
                    member = _archive_member_suffix(origin, path)
                    identity = (str(path.resolve()), member, name, kind)
                    if identity in unique_definitions:
                        continue
                    unique_definitions.add(identity)
                    providers[name].append(
                        {
                            "root": label,
                            "path": path.relative_to(root).as_posix(),
                            "member": member or None,
                            "nm_type": kind,
                        }
                    )
            except (
                OSError,
                RuntimeError,
                ValueError,
                subprocess.TimeoutExpired,
            ):
                errors.append(
                    {
                        "root": label,
                        "path": path.relative_to(root).as_posix(),
                        "error": "provider_inspection_failed",
                    }
                )

    matched = {}
    ambiguous = {}
    missing = {}
    categories = Counter()

    for name, consumers in sorted(data["undefined_without_aot_provider"].items()):
        if name.startswith(("nx::", "_ZN2nx", "_ZN3nx")):
            category = "nx_runtime"
        elif name.startswith(("plat::", "_ZN4plat")):
            category = "platform"
        elif name.startswith(("__cxa_", "__gxx_", "_Unwind_", "_Z", "std::")):
            category = "cxx_abi"
        elif name in {
            "ceil", "floor", "fma", "trunc", "sqrt", "sin",
            "cos", "pow", "round", "nearbyint",
        }:
            category = "libm"
        elif name.startswith("__atomic_"):
            category = "compiler_runtime"
        else:
            category = "c_or_other"
        categories[category] += 1

        row = {
            "consumers": consumers,
            "class": category,
            "providers": providers.get(name, []),
        }
        if not row["providers"]:
            missing[name] = row
        elif len(row["providers"]) > 1:
            # Multiple archive members count as multiple definitions even when
            # they live in the same .a file; a path-only count hid this case.
            ambiguous[name] = row
        else:
            matched[name] = row

    return {
        "audit_mode": "READ_ONLY_NM_PROVIDER_CANDIDATE_SCAN_NO_LINK",
        "inventory_root_name": data.get("root_name"),
        "inventory_object_count": data.get("totals", {}).get("object_copies_parsed"),
        "provider_roots": root_rows,
        "libraries_scanned": scanned,
        "defined_nm_entries_seen": symbols,
        "unique_provider_definitions_seen": len(unique_definitions),
        "aot_unresolved_symbol_count": len(data["undefined_without_aot_provider"]),
        "aot_unresolved_by_class": dict(sorted(categories.items())),
        "exact_provider_candidate_count": len(matched),
        "ambiguous_provider_candidate_count": len(ambiguous),
        "no_provider_candidate_count": len(missing),
        "matched_exact_names": matched,
        "ambiguous_exact_names": ambiguous,
        "no_exact_name_provider": missing,
        "library_scan_errors": errors,
        "all_provider_roots_scanned": not errors,
        "inputs_modified": False,
        "archives_extracted": False,
        "compilation_performed": False,
        "link_performed": False,
        "abi_compatibility_proven": False,
        "limitations": [
            "Exact-name matches are candidates, not proof of ABI compatibility.",
            "No relocation, symbol-version, calling-convention, type-layout, or transitive-dependency validation.",
            "Multiple definitions inside one archive are reported as ambiguous by member identity.",
            "The report contains private mangled names and local paths; keep it private.",
        ],
    }


def safe_report(path, protected, overwrite):
    destination = path.expanduser().absolute()
    if _has_symlink_component(destination.parent) or destination.is_symlink():
        raise ValueError("report_path_has_symlink_component")
    parent = destination.parent.resolve()
    if any(
        parent == root.resolve() or root.resolve() in parent.parents
        for root in protected
    ):
        raise ValueError("report_must_be_outside_inventory_and_provider_roots")
    if destination.exists() and not overwrite:
        base = destination
        number = 2
        while True:
            candidate = base.with_name(f"{base.stem}_v{number}{base.suffix}")
            if not candidate.exists() and not candidate.is_symlink():
                destination = candidate
                break
            number += 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def main():
    parser = argparse.ArgumentParser(
        description="Private read-only AOT/SDK provider candidate scan"
    )
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument(
        "--provider-root", action="append", required=True, metavar="LABEL=PATH"
    )
    parser.add_argument("--nm", default="llvm-nm")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--overwrite-report", action="store_true")
    args = parser.parse_args()

    tool = shutil.which(args.nm)
    if not tool:
        parser.error("nm_executable_not_found")
    if _has_symlink_component(args.inventory) or not args.inventory.is_file():
        parser.error("inventory_must_be_regular_file")

    try:
        data = json.loads(args.inventory.read_text(encoding="utf-8"))
        roots = []
        labels = set()
        for raw in args.provider_root:
            if "=" not in raw:
                parser.error("provider_root_must_be_LABEL_equals_PATH")
            label, raw_path = raw.split("=", 1)
            root = Path(raw_path).expanduser().absolute()
            if not label.strip() or label.strip() in labels:
                parser.error("provider_root_labels_must_be_nonempty_and_unique")
            if _has_symlink_component(root) or not root.is_dir():
                parser.error("invalid_provider_root")
            labels.add(label.strip())
            roots.append((label.strip(), root))

        result = scan(data, roots, tool)
        if not result["libraries_scanned"]:
            raise ValueError("no_provider_libraries_found")
        destination = safe_report(
            args.report, [args.inventory.parent, *(root for _, root in roots)],
            args.overwrite_report,
        )
        destination.write_text(
            json.dumps(result, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "status": (
                        "PROVIDER_SCAN_COMPLETE"
                        if result["all_provider_roots_scanned"]
                        else "PROVIDER_SCAN_INCOMPLETE"
                    ),
                    "libraries_scanned": result["libraries_scanned"],
                    "defined_nm_entries_seen": result["defined_nm_entries_seen"],
                    "unique_provider_definitions_seen": result[
                        "unique_provider_definitions_seen"
                    ],
                    "aot_unresolved_symbol_count": result[
                        "aot_unresolved_symbol_count"
                    ],
                    "exact_provider_candidate_count": result[
                        "exact_provider_candidate_count"
                    ],
                    "ambiguous_provider_candidate_count": result[
                        "ambiguous_provider_candidate_count"
                    ],
                    "no_provider_candidate_count": result[
                        "no_provider_candidate_count"
                    ],
                    "library_scan_error_count": len(result["library_scan_errors"]),
                    "abi_compatibility_proven": False,
                    "report_path": str(destination),
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        return 0 if result["all_provider_roots_scanned"] else 1
    except (OSError, json.JSONDecodeError, ValueError, subprocess.TimeoutExpired) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
