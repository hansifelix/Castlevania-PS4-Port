"""Synthetic tests for the OpenOrbis SDK symbol-provider inventory."""
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.ps4_sdk_symbol_provider_audit import (
    audit,
    parse_nm_defined_symbols,
    parse_undefined_symbols,
)


READELF = """Symbol table '.dynsym' contains 4 entries:
   Num:    Value          Size Type    Bind   Vis      Ndx Name
     1: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT  UND required_c
     2: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND sceGnmSubmitDone
     3: 0000000000000000     0 NOTYPE  WEAK   DEFAULT  UND optional_hook
     4: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND missing_runtime
Symbol table '.symtab' contains 2 entries:
   Num:    Value          Size Type    Bind   Vis      Ndx Name
     1: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT  UND required_c
     2: 0000000000000000     0 NOTYPE  WEAK   DEFAULT  UND optional_hook
"""


class SdkSymbolProviderAudit(unittest.TestCase):
    def test_readelf_extracts_strong_and_weak_imports_deduplicated(self):
        strong, weak = parse_undefined_symbols(READELF)
        self.assertEqual(strong, {"required_c", "sceGnmSubmitDone", "missing_runtime"})
        self.assertEqual(weak, {"optional_hook"})

    def test_nm_parser_uses_only_external_defined_symbols(self):
        text = """libsample.a[one.o]:
foo T 00000000 00000010
weak_hook W 00000000 00000004
not_defined U 00000000 00000000
local_symbol t 00000000 00000004
"""
        self.assertEqual(
            parse_nm_defined_symbols(text),
            {"foo", "weak_hook"},
        )

    def test_audit_maps_real_library_candidates_without_claiming_link_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "lib"
            root.mkdir()
            (root / "libc.a").write_bytes(b"fixture")
            (root / "libSceGnmDriver.so").write_bytes(b"fixture")
            (root / "libunused.a").write_bytes(b"fixture")

            def fake_nm(command, **kwargs):
                name = Path(command[-1]).name
                outputs = {
                    "libc.a": "required_c T 00000000 00000010\n",
                    "libSceGnmDriver.so": "sceGnmSubmitDone T 00000000 00000010\n",
                    "libunused.a": "unrelated T 00000000 00000010\n",
                }
                return SimpleNamespace(returncode=0, stdout=outputs[name], stderr="")

            report = audit(READELF, [root], runner=fake_nm)
            self.assertEqual(report["status"], "COMPLETE")
            self.assertEqual(report["strong_undefined_unique"], 3)
            self.assertEqual(report["weak_undefined_unique"], 1)
            self.assertEqual(report["strong_with_sdk_provider"], 2)
            self.assertEqual(report["strong_without_sdk_provider"], 1)
            self.assertEqual(report["libraries_scanned"], 3)
            self.assertEqual(report["classification"], "PRESENCE_ONLY_NOT_LINK_RESOLUTION")
            self.assertFalse(report["eboot_created"])
            self.assertFalse(report["pkg_created"])
            self.assertFalse(report["game_boot_verified"])
            self.assertEqual(report["drive_bytes_written"], 0)

    def test_multiple_candidate_libraries_are_reported_as_ambiguous(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "lib"
            root.mkdir()
            (root / "liba.a").write_bytes(b"fixture")
            (root / "libb.a").write_bytes(b"fixture")

            def fake_nm(command, **kwargs):
                return SimpleNamespace(
                    returncode=0,
                    stdout="required_c T 00000000 00000010\n",
                    stderr="",
                )

            report = audit(READELF, [root], runner=fake_nm)
            self.assertEqual(report["strong_with_multiple_sdk_providers"], 1)
            self.assertEqual(report["multiple_provider_examples"][0]["symbol"], "required_c")
            self.assertEqual(len(report["multiple_provider_examples"][0]["providers"]), 2)

    def test_partial_scan_is_not_reported_as_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "lib"
            root.mkdir()
            (root / "libbroken.a").write_bytes(b"fixture")

            def failed_nm(command, **kwargs):
                return SimpleNamespace(returncode=1, stdout="", stderr="bad archive")

            report = audit(READELF, [root], runner=failed_nm)
            self.assertEqual(report["status"], "PARTIAL_SCAN")
            self.assertEqual(report["library_scan_errors"], 1)
            self.assertFalse(report["eboot_created"])

    def test_missing_directory_and_malformed_readelf_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "absent"
            with self.assertRaises(ValueError):
                audit(READELF, [missing])
            with self.assertRaises(ValueError):
                parse_undefined_symbols("Symbol table '.symtab' contains 1 entries:\n  1: broken")


if __name__ == "__main__":
    unittest.main()
