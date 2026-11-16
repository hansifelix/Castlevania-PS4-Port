#!/usr/bin/env python3
"""Private evidence gate for reviewing exact-name AOT provider candidates.

Checks a manually prepared ABI evidence packet. It does not prove ABI
compatibility, invoke a linker, compile code, or create console packages.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path

SCHEMA = "kazuma-private-aot-abi-review-v1"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
CHECKS = (
    "sdk_version_verified", "target_abi_verified", "symbol_version_verified",
    "relocations_verified", "calling_convention_verified",
    "type_layout_verified", "transitive_dependencies_verified",
    "linker_resolution_reviewed",
)
VERDICTS = {"compatible", "incompatible", "insufficient_evidence"}


def has_symlink_component(path: Path) -> bool:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            return True
    return False


def nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def provider_key(row: dict) -> tuple:
    return row["root"], row["path"], row.get("member"), row["nm_type"]


def valid_provider(row) -> bool:
    return (
        isinstance(row, dict) and nonempty(row.get("root"))
        and nonempty(row.get("path")) and not Path(row["path"]).is_absolute()
        and ".." not in Path(row["path"]).parts
        and (row.get("member") is None or nonempty(row.get("member")))
        and isinstance(row.get("nm_type"), str) and len(row["nm_type"]) == 1
    )


def validate_provider_scan(scan: dict) -> tuple[dict, list[str]]:
    if not isinstance(scan, dict) or scan.get("audit_mode") != "READ_ONLY_NM_PROVIDER_CANDIDATE_SCAN_NO_LINK":
        raise ValueError("provider_scan_wrong_mode")
    if scan.get("all_provider_roots_scanned") is not True:
        raise ValueError("provider_scan_incomplete")
    if scan.get("library_scan_errors") != []:
        raise ValueError("provider_scan_has_errors")
    if scan.get("provider_tree_symlink_count") != 0 or scan.get("provider_tree_symlinks") != []:
        raise ValueError("provider_scan_has_skipped_symlinks")
    for flag in ("inputs_modified", "archives_extracted", "compilation_performed", "link_performed", "abi_compatibility_proven"):
        if scan.get(flag) is not False:
            raise ValueError("provider_scan_safety_flag_invalid")

    matched, ambiguous, missing = (
        scan.get("matched_exact_names"), scan.get("ambiguous_exact_names"),
        scan.get("no_exact_name_provider"),
    )
    if not all(isinstance(x, dict) for x in (matched, ambiguous, missing)):
        raise ValueError("provider_scan_candidate_maps_invalid")
    counts = {
        "exact_provider_candidate_count": len(matched),
        "ambiguous_provider_candidate_count": len(ambiguous),
        "no_provider_candidate_count": len(missing),
        "aot_unresolved_symbol_count": len(matched) + len(ambiguous) + len(missing),
    }
    for key, expected in counts.items():
        if type(scan.get(key)) is not int or scan[key] != expected:
            raise ValueError("provider_scan_count_mismatch")

    groups = (set(matched), set(ambiguous), set(missing))
    if (
        groups[0].intersection(groups[1])
        or groups[0].intersection(groups[2])
        or groups[1].intersection(groups[2])
    ):
        raise ValueError("provider_scan_symbol_in_multiple_groups")

    candidates = {}
    for group, data in (("matched", matched), ("ambiguous", ambiguous)):
        for symbol, item in data.items():
            rows = item.get("providers") if isinstance(item, dict) else None
            if not nonempty(symbol) or not isinstance(rows, list) or not rows:
                raise ValueError("provider_scan_candidate_record_invalid")
            if (group == "matched" and len(rows) != 1) or (group == "ambiguous" and len(rows) < 2):
                raise ValueError("provider_scan_candidate_cardinality_invalid")
            if any(not valid_provider(row) for row in rows):
                raise ValueError("provider_scan_provider_identity_invalid")
            keys = [provider_key(row) for row in rows]
            if len(keys) != len(set(keys)):
                raise ValueError("provider_scan_duplicate_provider_identity")
            candidates[symbol] = rows

    no_provider = []
    for symbol, item in missing.items():
        if not nonempty(symbol) or not isinstance(item, dict) or item.get("providers") != []:
            raise ValueError("provider_scan_missing_symbol_invalid")
        no_provider.append(symbol)
    if set(candidates).intersection(no_provider):
        raise ValueError("provider_scan_symbol_in_multiple_groups")
    return candidates, sorted(no_provider)


def validate_header(evidence: dict) -> list[str]:
    if not isinstance(evidence, dict) or not nonempty(evidence.get("header_path")):
        raise ValueError("abi_header_path_missing")
    path = Path(evidence["header_path"]).expanduser()
    if not path.is_absolute() or has_symlink_component(path) or not path.is_file():
        raise ValueError("abi_header_path_not_regular_file")

    header_hash, declaration_hash = evidence.get("header_sha256"), evidence.get("declaration_sha256")
    if not isinstance(header_hash, str) or not SHA256.fullmatch(header_hash):
        raise ValueError("abi_header_sha256_invalid")
    if not isinstance(declaration_hash, str) or not SHA256.fullmatch(declaration_hash):
        raise ValueError("abi_declaration_sha256_invalid")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != header_hash:
        raise ValueError("abi_header_sha256_mismatch")
    start, end = evidence.get("declaration_start_line"), evidence.get("declaration_end_line")
    if type(start) is not int or type(end) is not int or start < 1 or end < start:
        raise ValueError("abi_declaration_line_range_invalid")
    lines = raw.splitlines(keepends=True)
    if end > len(lines):
        raise ValueError("abi_declaration_line_range_out_of_bounds")
    snippet = b"".join(lines[start - 1:end])
    if hashlib.sha256(snippet).hexdigest() != declaration_hash:
        raise ValueError("abi_declaration_sha256_mismatch")
    if not nonempty(evidence.get("symbol_version")) or not nonempty(evidence.get("calling_convention")):
        raise ValueError("abi_symbol_or_calling_convention_missing")
    if not all(type(evidence.get(name)) is bool for name in CHECKS):
        raise ValueError("abi_review_checks_must_be_explicit_booleans")
    return [name for name in CHECKS if evidence[name] is not True]


def validate_packet(scan: dict, packet: dict, scan_hash: str) -> dict:
    candidates, no_provider = validate_provider_scan(scan)
    if not isinstance(packet, dict) or packet.get("schema") != SCHEMA:
        raise ValueError("abi_review_schema_invalid")
    if packet.get("provider_scan_sha256") != scan_hash:
        raise ValueError("abi_provider_scan_sha256_mismatch")
    target = packet.get("target")
    required_target = ("sdk_release", "compiler", "target_triple", "runtime_revision")
    if not isinstance(target, dict) or not all(nonempty(target.get(k)) for k in required_target):
        raise ValueError("abi_target_identity_incomplete")

    rows = packet.get("candidate_reviews")
    if not isinstance(rows, list):
        raise ValueError("abi_candidate_reviews_not_list")
    expected = {(symbol, provider_key(p)) for symbol, providers in candidates.items() for p in providers}
    seen, compatible = set(), {symbol: 0 for symbol in candidates}
    incompatible = insufficient = 0
    evidence_failures = []

    for row in rows:
        if not isinstance(row, dict) or not nonempty(row.get("symbol")) or not valid_provider(row.get("provider")):
            raise ValueError("abi_candidate_review_invalid")
        key = (row["symbol"], provider_key(row["provider"]))
        if key not in expected:
            raise ValueError("abi_review_provider_not_in_scan")
        if key in seen:
            raise ValueError("abi_duplicate_candidate_review")
        seen.add(key)
        verdict = row.get("verdict")
        if verdict not in VERDICTS:
            raise ValueError("abi_review_verdict_invalid")
        if not nonempty(row.get("reviewer")) or not nonempty(row.get("reviewed_at")):
            raise ValueError("abi_reviewer_or_timestamp_missing")
        try:
            timestamp = datetime.fromisoformat(row["reviewed_at"].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("abi_review_timestamp_invalid") from exc
        if timestamp.tzinfo is None:
            raise ValueError("abi_review_timestamp_requires_timezone")

        failed = validate_header(row.get("evidence"))
        if verdict == "compatible":
            if failed:
                evidence_failures.append({"symbol": row["symbol"], "reason": "compatible_verdict_has_unverified_checks"})
            else:
                compatible[row["symbol"]] += 1
        elif verdict == "incompatible":
            if not nonempty(row.get("reason")):
                raise ValueError("abi_incompatible_verdict_requires_reason")
            if not failed:
                evidence_failures.append({"symbol": row["symbol"], "reason": "incompatible_verdict_has_all_checks_verified"})
            incompatible += 1
        else:
            insufficient += 1

    missing_reviews = len(expected - seen)
    unreviewed = sorted({symbol for symbol, _ in expected - seen})
    multiple = sorted(symbol for symbol, count in compatible.items() if count > 1)
    unresolved = sorted(symbol for symbol, count in compatible.items() if count == 0)
    complete = (
        missing_reviews == 0 and not evidence_failures and not multiple
        and not unresolved and not no_provider and insufficient == 0
    )
    return {
        "audit_mode": "PRIVATE_ABI_EVIDENCE_REVIEW_NO_COMPILE_NO_LINK",
        "provider_scan_sha256": scan_hash,
        "target": target,
        "candidate_symbol_count": len(candidates),
        "candidate_definition_count": len(expected),
        "no_provider_symbol_count": len(no_provider),
        "candidate_reviews_received": len(rows),
        "candidate_reviews_missing": missing_reviews,
        "unreviewed_symbol_count": len(unreviewed),
        "compatible_definition_count": sum(compatible.values()),
        "incompatible_definition_count": incompatible,
        "insufficient_evidence_count": insufficient,
        "symbols_with_multiple_compatible_definitions": len(multiple),
        "symbols_without_one_compatible_definition": len(unresolved),
        "evidence_failure_count": len(evidence_failures),
        "review_complete": complete,
        "status": "ABI_EVIDENCE_REVIEW_COMPLETE_NOT_LINK_PROOF" if complete else "ABI_EVIDENCE_REVIEW_BLOCKED",
        "abi_compatibility_proven": False,
        "link_authorized": False,
        "compilation_performed": False,
        "link_performed": False,
        "eboot_created": False,
        "pkg_created": False,
        "ps4_tested": False,
        "private_details": {
            "unreviewed_symbols": unreviewed,
            "symbols_without_compatible_provider": unresolved,
            "symbols_with_multiple_compatible_providers": multiple,
            "no_provider_symbols": no_provider,
            "evidence_failures": evidence_failures,
        },
        "limitations": [
            "This gate checks evidence packet completeness and local header hashes; it does not independently prove ABI compatibility.",
            "A human reviewer remains responsible for the correctness of every verified check.",
            "No relocation processing, compilation, linking, EBOOT/PKG creation, PS4 installation, boot, or gameplay is performed.",
            "The report contains private symbol names and local header paths; keep it outside public repositories and artifacts.",
        ],
    }


def safe_report(path: Path, protected: list[Path], overwrite: bool) -> Path:
    destination = path.expanduser().absolute()
    if has_symlink_component(destination.parent) or destination.is_symlink():
        raise ValueError("report_path_has_symlink_component")
    parent = destination.parent.resolve()
    for item in protected:
        resolved = item.expanduser().resolve()
        if destination.resolve() == resolved or parent == resolved or resolved in parent.parents:
            raise ValueError("report_must_be_outside_input_and_evidence_roots")
    if destination.exists() and not overwrite:
        base, version = destination, 2
        while True:
            candidate = base.with_name(f"{base.stem}_v{version}{base.suffix}")
            if not candidate.exists() and not candidate.is_symlink():
                destination = candidate
                break
            version += 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Private read-only AOT ABI evidence gate")
    parser.add_argument("--provider-scan", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--overwrite-report", action="store_true")
    args = parser.parse_args()
    for source in (args.provider_scan, args.reviews):
        if has_symlink_component(source) or not source.is_file():
            parser.error("input_must_be_regular_non_symlink_file")
    try:
        scan_bytes = args.provider_scan.read_bytes()
        scan = json.loads(scan_bytes.decode("utf-8"))
        packet = json.loads(args.reviews.read_text(encoding="utf-8"))
        scan_hash = hashlib.sha256(scan_bytes).hexdigest()
        result = validate_packet(scan, packet, scan_hash)
        evidence_files = [Path(row["evidence"]["header_path"]).expanduser() for row in packet["candidate_reviews"]]
        destination = safe_report(args.report, [args.provider_scan.parent, args.reviews.parent, *evidence_files], args.overwrite_report)
        destination.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": result["status"],
            "candidate_symbol_count": result["candidate_symbol_count"],
            "candidate_definition_count": result["candidate_definition_count"],
            "candidate_reviews_received": result["candidate_reviews_received"],
            "candidate_reviews_missing": result["candidate_reviews_missing"],
            "no_provider_symbol_count": result["no_provider_symbol_count"],
            "compatible_definition_count": result["compatible_definition_count"],
            "incompatible_definition_count": result["incompatible_definition_count"],
            "insufficient_evidence_count": result["insufficient_evidence_count"],
            "evidence_failure_count": result["evidence_failure_count"],
            "abi_compatibility_proven": False,
            "link_authorized": False,
            "report_path": str(destination),
        }, ensure_ascii=True, indent=2))
        return 0 if result["review_complete"] else 1
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
