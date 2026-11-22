import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from tools.link.private_aot_provider_hash_join import (
    JoinError,
    join_inventory,
    load_inventory,
    validate_provider_manifest,
    write_report,
    main,
)


def digest(name):
    return hashlib.sha256(name.encode("utf-8")).hexdigest()


def provider_manifest(names, scope="SYNTHETIC_PROVIDER"):
    rows = []
    for name, definitions, kinds in names:
        rows.append({
            "sha256": digest(name),
            "definition_count": definitions,
            "kinds": kinds,
        })
    rows.sort(key=lambda row: row["sha256"])
    canonical = "".join(
        f'{row["sha256"]}:{row["definition_count"]}:{",".join(row["kinds"])}\n'
        for row in rows
    )
    return {
        "schema_version": 1,
        "provider_scope": scope,
        "hash_algorithm": "SHA-256 of exact UTF-8 symbol name",
        "symbol_names_included": False,
        "provider_paths_included": False,
        "private_aot_data_included": False,
        "scan_complete": True,
        "abi_compatibility_proven": False,
        "unique_symbol_hash_count": len(rows),
        "symbol_hashes": rows,
        "symbol_hash_manifest_sha256": hashlib.sha256(canonical.encode("ascii")).hexdigest(),
    }


def inventory():
    return {
        "audit_mode": "READ_ONLY_SYMBOL_TABLE_PARSE_NO_EXTRACT_NO_COMPILE_NO_LINK",
        "index_coverage_complete": True,
        "duplicate_metadata_complete": True,
        "invalid_objects": [],
        "private_symbol_names_in_report": True,
        "inputs_modified": False,
        "files_extracted": False,
        "compilation_performed": False,
        "link_performed": False,
        "totals": {"undefined_symbols_without_provider_in_aot_inventory": 3},
        "undefined_without_aot_provider": {
            "nx::synthetic_runtime": ["main:1", "sdk:2"],
            "__cxa_synthetic": ["main:3"],
            "unmatched_synthetic": ["subsdk0:4", "subsdk0:5"],
        },
    }


class PrivateHashJoinTests(unittest.TestCase):
    def test_join_emits_aggregate_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inv_path = root / "input" / "inventory.json"
            prov_path = root / "provider" / "manifest.json"
            inv_path.parent.mkdir()
            prov_path.parent.mkdir()
            inv_path.write_text(json.dumps(inventory()), encoding="utf-8")
            prov = provider_manifest([
                ("__cxa_synthetic", 2, ["T"]),
                ("nx::synthetic_runtime", 1, ["T"]),
            ])
            prov_path.write_text(json.dumps(prov), encoding="utf-8")
            _, pending = load_inventory(inv_path)
            data, index, file_hash = validate_provider_manifest(prov_path)
            result = join_inventory(pending, index, data["provider_scope"], file_hash)
            self.assertEqual(result["aot_unresolved_unique_names"], 3)
            self.assertEqual(result["exact_name_hash_matches"], 2)
            self.assertEqual(result["no_provider_hash_match"], 1)
            self.assertEqual(result["matched_definition_count_total"], 3)
            self.assertEqual(result["matched_names_with_multiple_definitions"], 1)
            self.assertEqual(result["matched_names_with_single_definition"], 1)
            self.assertEqual(result["matched_consumer_references"], 3)
            self.assertEqual(result["unmatched_consumer_references"], 2)
            serialized = json.dumps(result)
            self.assertNotIn("nx::synthetic_runtime", serialized)
            self.assertNotIn("__cxa_synthetic", serialized)
            self.assertNotIn("unmatched_synthetic", serialized)
            self.assertNotIn(digest("nx::synthetic_runtime"), serialized)

    def test_provider_manifest_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            data = provider_manifest([("synthetic", 1, ["T"])])
            data["symbol_hash_manifest_sha256"] = "0" * 64
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(JoinError, "PROVIDER_MANIFEST_HASH_MISMATCH"):
                validate_provider_manifest(path)

    def test_manifest_with_symbol_names_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            data = provider_manifest([("synthetic", 1, ["T"])])
            data["symbol_names_included"] = True
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(JoinError, "PROVIDER_MANIFEST_NOT_COMPLETE_HASH_ONLY"):
                validate_provider_manifest(path)

    def test_inventory_with_compile_or_link_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inventory.json"
            data = inventory()
            data["link_performed"] = True
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(JoinError, "PRIVATE_INVENTORY_NOT_COMPLETE_READ_ONLY"):
                load_inventory(path)

    def test_report_cannot_be_written_under_private_input_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            root.mkdir()
            inv = root / "inventory.json"
            inv.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(JoinError, "REPORT_MUST_BE_OUTSIDE_INPUT_ROOTS"):
                write_report(root / "report.json", {}, [root])

    def test_cli_allows_drive_root_report_outside_private_aot_subfolder(self):
        with tempfile.TemporaryDirectory() as tmp:
            drive = Path(tmp) / "drive"
            drive.mkdir()
            private_root = drive / "Kazuma_Traducoes_AOT_Privado"
            private_root.mkdir()
            inventory_path = drive / "RELATORIO_SIMBOLOS_ETAPA91_PRIVADO.json"
            inventory_path.write_text(json.dumps(inventory()), encoding="utf-8")
            provider_root = Path(tmp) / "provider"
            provider_root.mkdir()
            provider_path = provider_root / "manifest.json"
            provider_path.write_text(json.dumps(provider_manifest([
                ("__cxa_synthetic", 2, ["T"]),
                ("nx::synthetic_runtime", 1, ["T"]),
            ])), encoding="utf-8")
            report_path = drive / "RELATORIO_HASH_JOIN.json"
            argv = [
                "join", "--inventory", str(inventory_path),
                "--private-root", str(private_root),
                "--provider-manifest", str(provider_path),
                "--report", str(report_path),
            ]
            output = StringIO()
            with patch("sys.argv", argv), redirect_stdout(output):
                rc = main()
            self.assertEqual(rc, 0)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["provider_results"][0]["exact_name_hash_matches"], 2)
            self.assertEqual(report["provider_results"][0]["no_provider_hash_match"], 1)
            self.assertFalse(report["private_symbol_names_included"])
            self.assertFalse(report["private_symbol_hashes_included"])
            self.assertNotIn("nx::synthetic_runtime", report_path.read_text(encoding="utf-8"))
            self.assertIn("PRIVATE_HASH_JOIN_COMPLETE", output.getvalue())

    def test_cli_blocks_report_inside_private_aot_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            drive = Path(tmp) / "drive"
            drive.mkdir()
            private_root = drive / "Kazuma_Traducoes_AOT_Privado"
            private_root.mkdir()
            inventory_path = drive / "RELATORIO_SIMBOLOS_ETAPA91_PRIVADO.json"
            inventory_path.write_text(json.dumps(inventory()), encoding="utf-8")
            provider_root = Path(tmp) / "provider"
            provider_root.mkdir()
            provider_path = provider_root / "manifest.json"
            provider_path.write_text(json.dumps(provider_manifest([
                ("__cxa_synthetic", 2, ["T"]),
            ])), encoding="utf-8")
            report_path = private_root / "RELATORIO_HASH_JOIN.json"
            argv = [
                "join", "--inventory", str(inventory_path),
                "--private-root", str(private_root),
                "--provider-manifest", str(provider_path),
                "--report", str(report_path),
            ]
            output = StringIO()
            with patch("sys.argv", argv), redirect_stdout(output):
                rc = main()
            self.assertEqual(rc, 2)
            self.assertFalse(report_path.exists())
            self.assertIn("REPORT_MUST_BE_OUTSIDE_INPUT_ROOTS", output.getvalue())


if __name__ == "__main__":
    unittest.main()
