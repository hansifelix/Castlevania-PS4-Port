import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.classify_public_link import PRIVATE_AOT, classify


def strict_report(undefined=None):
    return {
        "status": "BLOCKED",
        "linker_exit_code": 1,
        "all_undefined_symbols": sorted(PRIVATE_AOT if undefined is None else set(undefined)),
        "all_duplicate_symbols": [],
        "all_missing_libraries": [],
        "all_other_errors": [],
        "duplicate_symbols_reported": 0,
        "missing_libraries_reported": 0,
        "other_linker_errors_reported": 0,
        "output_path": "/dev/null",
        "elf_output_saved": False,
        "eboot_created": False,
        "pkg_created": False,
        "private_objects_uploaded": False,
        "drive_bytes_written": 0,
    }


class ClassifyPublicLinkTests(unittest.TestCase):
    def test_only_three_private_aot_references_is_public_closure(self):
        result = classify(strict_report())
        self.assertEqual(result["status"], "PUBLIC_LINK_CLOSED_AOT_PENDING")
        self.assertEqual(result["unresolved_private_aot"], sorted(PRIVATE_AOT))
        self.assertFalse(result["strict_executable_link_passed"])
        self.assertFalse(result["eboot_created"])
        self.assertFalse(result["pkg_created"])

    def test_unexpected_public_symbol_stays_red(self):
        result = classify(strict_report(set(PRIVATE_AOT) | {"orbis_sysconf"}))
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("orbis_sysconf", result["unexpected_unresolved_symbols"])

    def test_missing_private_aot_reference_stays_red(self):
        result = classify(strict_report({"nx_module_main", "nx_module_sdk"}))
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("nx_module_subsdk0", result["private_aot_references_missing"])

    def test_duplicate_or_missing_library_stays_red(self):
        report = strict_report()
        report["all_duplicate_symbols"] = ["duplicate"]
        result = classify(report)
        self.assertEqual(result["status"], "FAIL")

        report = strict_report()
        report["all_missing_libraries"] = ["SceVideoOut"]
        result = classify(report)
        self.assertEqual(result["status"], "FAIL")

    def test_saved_elf_or_non_diskless_output_stays_red(self):
        report = strict_report()
        report["elf_output_saved"] = True
        result = classify(report)
        self.assertEqual(result["status"], "FAIL")

        report = strict_report()
        report["output_path"] = "game.elf"
        result = classify(report)
        self.assertEqual(result["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
