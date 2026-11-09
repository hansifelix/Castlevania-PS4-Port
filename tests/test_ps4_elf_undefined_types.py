"""Synthetic readelf symbol-type audit tests."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.ps4_elf_undefined_types import inspect


FIXTURE = """Symbol table '.dynsym' contains 4 entries:
   Num:    Value          Size Type    Bind   Vis      Ndx Name
     1: 0000000000000000     0 NOTYPE  WEAK   DEFAULT  UND weak_notype
     2: 0000000000000000     0 FUNC    WEAK   DEFAULT  UND weak_function
     3: 0000000000000000     0 OBJECT  WEAK   DEFAULT  UND weak_object
     4: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND strong_function
Symbol table '.symtab' contains 2 entries:
   Num:    Value          Size Type    Bind   Vis      Ndx Name
     1: 0000000000000000     0 NOTYPE  WEAK   DEFAULT  UND weak_notype
     2: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND strong_function
"""


class UndefinedElfTypes(unittest.TestCase):
    def test_counts_distinct_weak_and_strong_by_elf_type(self):
        report = inspect(FIXTURE)
        self.assertEqual(report["weak_undefined_distinct"], 3)
        self.assertEqual(report["strong_undefined_distinct"], 1)
        self.assertEqual(report["weak_notype_count"], 1)
        self.assertEqual(report["weak_function_count"], 1)
        self.assertEqual(report["weak_object_count"], 1)
        self.assertEqual(report["classification"],
                         "ELF_TYPE_INVENTORY_ONLY_NOT_SEMANTIC_VALIDATION")

    def test_duplicate_dynsym_and_symtab_rows_are_deduplicated(self):
        report = inspect(FIXTURE)
        self.assertEqual(report["parsed_symbol_rows"], 6)
        self.assertEqual(report["weak_undefined_distinct"] +
                         report["strong_undefined_distinct"], 4)

    def test_malformed_symbol_row_fails_closed(self):
        bad = "Symbol table '.symtab' contains 1 entries:\n  1: broken"
        with self.assertRaises(ValueError):
            inspect(bad)

    def test_no_runtime_or_converter_success_is_claimed(self):
        report = inspect(FIXTURE)
        self.assertFalse(report["create_fself_compatibility_proven"])
        self.assertFalse(report["weak_absent_semantics_proven"])
        self.assertFalse(report["game_boot_verified"])
        self.assertFalse(report["eboot_created"])
        self.assertFalse(report["pkg_created"])
        self.assertEqual(report["drive_bytes_written"], 0)


if __name__ == "__main__":
    unittest.main()
