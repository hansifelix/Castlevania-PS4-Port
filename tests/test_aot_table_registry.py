"""Tests with synthetic table.cpp text; no commercial code."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.etapa87.check_aot_table import verify_table


def fake_table(entries: list[tuple[int, str]]) -> str:
    body = "\n".join(f"    {{{o:#x}, {n}}}," for o, n in entries)
    return (
        '#include "funcs.h"\n#include <nx/module.h>\n'
        f'static const nx::FuncEntry funcs[] = {{\n{body}\n}};\n'
        'extern const nx::ModuleInfo nx_module_subsdk0 = {};\n'
    )


class TableContract(unittest.TestCase):
    def test_consistent_table(self):
        source = fake_table([(0, "subsdk0_00000000"),
                             (0x24, "subsdk0_00000024")])
        report = "functions 2, handled 100, unhandled 0\n"
        result = verify_table(source, report, "subsdk0")
        self.assertEqual(result["table_function_count"], 2)
        self.assertEqual(result["last_offset"], "0x24")
        self.assertFalse(result["linked_to_runtime"])

    def test_duplicate_offset_rejected(self):
        source = fake_table([(0, "subsdk0_00000000"),
                             (0, "subsdk0_00000000")])
        with self.assertRaisesRegex(ValueError, "duplicados"):
            verify_table(source, "functions 2, handled 100, unhandled 0", "subsdk0")

    def test_count_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "difere"):
            verify_table(fake_table([(0, "subsdk0_00000000")]),
                         "functions 2, handled 100, unhandled 0", "subsdk0")

    def test_other_module_rejected(self):
        with self.assertRaisesRegex(ValueError, "não pertence"):
            verify_table(fake_table([(0, "sdk_00000000")]),
                         "functions 1, handled 100, unhandled 0", "subsdk0")

    def test_symbol_offset_mismatch(self):
        with self.assertRaisesRegex(ValueError, "Offset"):
            verify_table(fake_table([(0x20, "subsdk0_00000024")]),
                         "functions 1, handled 100, unhandled 0", "subsdk0")

    def test_missing_registry_symbol(self):
        t = fake_table([(0, "subsdk0_00000000")])
        t = t.replace("nx_module_subsdk0", "nx_module_missing")
        with self.assertRaisesRegex(ValueError, "Metadados"):
            verify_table(t, "functions 1, handled 10, unhandled 0", "subsdk0")

    def test_unrecognized_content_rejected(self):
        t = fake_table([(0, "subsdk0_00000000")])
        t = t.replace("};", "not-an-entry\n};", 1)
        with self.assertRaisesRegex(ValueError, "não reconhecidas"):
            verify_table(t, "functions 1, handled 10, unhandled 0", "subsdk0")

    def test_unhandled_count_is_preserved(self):
        r = verify_table(fake_table([(0, "subsdk0_00000000")]),
                         "functions 1, handled 10, unhandled 3", "subsdk0")
        self.assertEqual(r["unhandled_reported"], 3)
        self.assertFalse(r["eboot_created"])


if __name__ == "__main__":
    unittest.main()
