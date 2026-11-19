import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.etapa90.private_aot_abi_evidence_gate import SCHEMA, validate_provider_scan, validate_packet


def p(root, path, member, kind="T"):
    return {"root": root, "path": path, "member": member, "nm_type": kind}


def sample_scan(missing=False):
    matched = {"_Zone": {"providers": [p("sdk", "lib/a.a", "a.o")]}}
    ambiguous = {"_Ztwo": {"providers": [p("sdk", "lib/b.a", "b1.o"), p("runtime", "lib/c.a", "b2.o", "W")]}}
    no_provider = {"_Znone": {"providers": []}} if missing else {}
    return {
        "audit_mode": "READ_ONLY_NM_PROVIDER_CANDIDATE_SCAN_NO_LINK",
        "all_provider_roots_scanned": True, "library_scan_errors": [],
        "provider_tree_symlink_count": 0, "provider_tree_symlinks": [],
        "inputs_modified": False, "archives_extracted": False,
        "compilation_performed": False, "link_performed": False,
        "abi_compatibility_proven": False,
        "matched_exact_names": matched, "ambiguous_exact_names": ambiguous,
        "no_exact_name_provider": no_provider,
        "exact_provider_candidate_count": len(matched),
        "ambiguous_provider_candidate_count": len(ambiguous),
        "no_provider_candidate_count": len(no_provider),
        "aot_unresolved_symbol_count": len(matched) + len(ambiguous) + len(no_provider),
    }


def evidence(header, valid=True):
    raw = header.read_bytes()
    checks = (
        "sdk_version_verified", "target_abi_verified", "symbol_version_verified",
        "relocations_verified", "calling_convention_verified", "type_layout_verified",
        "transitive_dependencies_verified", "linker_resolution_reviewed",
    )
    result = {
        "header_path": str(header),
        "header_sha256": hashlib.sha256(raw).hexdigest(),
        "declaration_start_line": 1, "declaration_end_line": 1,
        "declaration_sha256": hashlib.sha256(raw.splitlines(keepends=True)[0]).hexdigest(),
        "symbol_version": "none (verified)", "calling_convention": "cdecl",
    }
    result.update({name: valid for name in checks})
    return result


def packet_for(scan, scan_hash, header, both_compatible=False):
    return {
        "schema": SCHEMA,
        "provider_scan_sha256": scan_hash,
        "target": {"sdk_release": "OpenOrbis 0.5.4", "compiler": "Clang 18",
                   "target_triple": "x86_64-scei-ps4", "runtime_revision": "fixture-revision"},
        "candidate_reviews": [
            {"symbol": "_Zone", "provider": p("sdk", "lib/a.a", "a.o"),
             "verdict": "compatible", "evidence": evidence(header),
             "reviewer": "reviewer-a", "reviewed_at": "2026-11-16T19:00:00-03:00"},
            {"symbol": "_Ztwo", "provider": p("sdk", "lib/b.a", "b1.o"),
             "verdict": "compatible", "evidence": evidence(header),
             "reviewer": "reviewer-a", "reviewed_at": "2026-11-16T19:01:00-03:00"},
            {"symbol": "_Ztwo", "provider": p("runtime", "lib/c.a", "b2.o", "W"),
             "verdict": "compatible" if both_compatible else "incompatible",
             "evidence": evidence(header, valid=both_compatible),
             "reason": "Alternate provider fails the target ABI review.",
             "reviewer": "reviewer-a", "reviewed_at": "2026-11-16T19:02:00-03:00"},
        ],
    }


class AbiEvidenceGateTests(unittest.TestCase):
    def test_scan_requires_complete_and_consistent_counts(self):
        scan = sample_scan()
        candidates, missing = validate_provider_scan(scan)
        self.assertEqual(set(candidates), {"_Zone", "_Ztwo"})
        self.assertEqual(len(candidates["_Ztwo"]), 2)
        self.assertEqual(missing, [])
        scan["aot_unresolved_symbol_count"] += 1
        with self.assertRaisesRegex(ValueError, "count_mismatch"):
            validate_provider_scan(scan)

    def test_symbol_cannot_appear_in_multiple_provider_groups(self):
        scan = sample_scan()
        scan["ambiguous_exact_names"]["_Zone"] = {
            "providers": [p("sdk", "lib/x.a", "x1.o"), p("sdk", "lib/x.a", "x2.o")]
        }
        scan["ambiguous_provider_candidate_count"] = len(scan["ambiguous_exact_names"])
        scan["aot_unresolved_symbol_count"] = (
            len(scan["matched_exact_names"]) + len(scan["ambiguous_exact_names"])
            + len(scan["no_exact_name_provider"])
        )
        with self.assertRaisesRegex(ValueError, "symbol_in_multiple_groups"):
            validate_provider_scan(scan)

    def test_skipped_symlink_blocks_the_scan(self):
        scan = sample_scan()
        scan["provider_tree_symlink_count"] = 1
        scan["provider_tree_symlinks"] = [{"root": "sdk", "path": "alias", "kind": "directory"}]
        with self.assertRaisesRegex(ValueError, "skipped_symlinks"):
            validate_provider_scan(scan)

    def test_complete_evidence_packet_does_not_authorize_link(self):
        scan = sample_scan()
        scan_hash = hashlib.sha256(json.dumps(scan, sort_keys=True).encode()).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            header = Path(td) / "api.h"
            header.write_text("int api(void);\n", encoding="utf-8")
            result = validate_packet(scan, packet_for(scan, scan_hash, header), scan_hash)
        self.assertTrue(result["review_complete"])
        self.assertEqual(result["status"], "ABI_EVIDENCE_REVIEW_COMPLETE_NOT_LINK_PROOF")
        self.assertFalse(result["abi_compatibility_proven"])
        self.assertFalse(result["link_authorized"])
        self.assertFalse(result["link_performed"])

    def test_packet_must_bind_to_exact_provider_report_hash(self):
        scan = sample_scan()
        with tempfile.TemporaryDirectory() as td:
            header = Path(td) / "api.h"
            header.write_text("int api(void);\n", encoding="utf-8")
            packet = packet_for(scan, "0" * 64, header)
            with self.assertRaisesRegex(ValueError, "sha256_mismatch"):
                validate_packet(scan, packet, "1" * 64)

    def test_all_archive_members_need_reviews(self):
        scan = sample_scan()
        scan_hash = hashlib.sha256(json.dumps(scan, sort_keys=True).encode()).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            header = Path(td) / "api.h"
            header.write_text("int api(void);\n", encoding="utf-8")
            packet = packet_for(scan, scan_hash, header)
            packet["candidate_reviews"].pop()
            result = validate_packet(scan, packet, scan_hash)
        self.assertFalse(result["review_complete"])
        self.assertEqual(result["candidate_reviews_missing"], 1)

    def test_two_compatible_archive_members_remain_ambiguous(self):
        scan = sample_scan()
        scan_hash = hashlib.sha256(json.dumps(scan, sort_keys=True).encode()).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            header = Path(td) / "api.h"
            header.write_text("int api(void);\n", encoding="utf-8")
            result = validate_packet(scan, packet_for(scan, scan_hash, header, True), scan_hash)
        self.assertFalse(result["review_complete"])
        self.assertEqual(result["symbols_with_multiple_compatible_definitions"], 1)

    def test_no_provider_symbol_blocks_completion(self):
        scan = sample_scan(missing=True)
        scan_hash = hashlib.sha256(json.dumps(scan, sort_keys=True).encode()).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            header = Path(td) / "api.h"
            header.write_text("int api(void);\n", encoding="utf-8")
            result = validate_packet(scan, packet_for(scan, scan_hash, header), scan_hash)
        self.assertFalse(result["review_complete"])
        self.assertEqual(result["no_provider_symbol_count"], 1)

    def test_modified_header_fails_hash_check(self):
        scan = sample_scan()
        scan_hash = hashlib.sha256(json.dumps(scan, sort_keys=True).encode()).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            header = Path(td) / "api.h"
            header.write_text("int api(void);\n", encoding="utf-8")
            packet = packet_for(scan, scan_hash, header)
            header.write_text("int api(int changed);\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "header_sha256_mismatch"):
                validate_packet(scan, packet, scan_hash)

    def test_review_timestamp_requires_timezone(self):
        scan = sample_scan()
        scan_hash = hashlib.sha256(json.dumps(scan, sort_keys=True).encode()).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            header = Path(td) / "api.h"
            header.write_text("int api(void);\n", encoding="utf-8")
            packet = packet_for(scan, scan_hash, header)
            packet["candidate_reviews"][0]["reviewed_at"] = "2026-11-16T19:00:00"
            with self.assertRaisesRegex(ValueError, "requires_timezone"):
                validate_packet(scan, packet, scan_hash)

    def test_compatible_verdict_requires_all_review_checks(self):
        scan = sample_scan()
        scan_hash = hashlib.sha256(json.dumps(scan, sort_keys=True).encode()).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            header = Path(td) / "api.h"
            header.write_text("int api(void);\n", encoding="utf-8")
            packet = packet_for(scan, scan_hash, header)
            packet["candidate_reviews"][0]["evidence"]["relocations_verified"] = False
            result = validate_packet(scan, packet, scan_hash)
        self.assertFalse(result["review_complete"])
        self.assertEqual(result["evidence_failure_count"], 1)


if __name__ == "__main__":
    unittest.main()
