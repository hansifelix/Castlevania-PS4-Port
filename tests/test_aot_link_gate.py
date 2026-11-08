"""Fixtures 100% sinteticas: avaliam o gate sem acesso a dados de jogos."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.aot_link_gate import inspect

BASE = """0000 T main_00000000(nx::CPU&)
0008 T main_00000008(nx::CPU&)
0010 T sdk_00000000(nx::CPU&)
0020 T subsdk0_00000000(nx::CPU&)
0030 D nx_module_main
0040 D nx_module_sdk
0050 D nx_module_subsdk0
0060 T nx::linked_modules()
0070 T nx::call(nx::CPU&, unsigned long)
0080 T nx::unimpl(nx::CPU&, unsigned long, char const*)
"""
EXPECTED = {"main": 2, "sdk": 1, "subsdk0": 1}

def eval_fake(defs: str, undefs: str, expected=EXPECTED):
    with tempfile.TemporaryDirectory() as temp:
        d, u = Path(temp) / "defined.txt", Path(temp) / "undefined.txt"
        d.write_text(defs)
        u.write_text(undefs)
        return inspect(d, u, expected)

class AotLinkGateTest(unittest.TestCase):
    def test_pass_with_standard_runtime_externals(self):
        r = eval_fake(BASE, "  U ceil\n  U __cxa_throw\n")
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["total_guest_definitions"], 4)
        self.assertEqual(r["other_external_symbol_names_not_disclosed"], 2)

    def test_missing_guest_function_fails(self):
        r = eval_fake(BASE, "  U main_00000010(nx::CPU&)\n")
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual(r["guest_undefined_count"], 1)

    def test_missing_table_fails(self):
        r = eval_fake(BASE.replace("0030 D nx_module_main\n", ""), "  U nx_module_main\n")
        self.assertEqual(r["status"], "FAIL")

    def test_wrong_counts_fail(self):
        self.assertEqual(eval_fake(BASE, "", {"main": 3, "sdk": 1, "subsdk0": 1})["status"], "FAIL")

    def test_missing_loader_runtime_fails(self):
        self.assertEqual(eval_fake(BASE.replace("0070 T nx::call(nx::CPU&, unsigned long)\n", ""), "")["status"], "FAIL")

    def test_duplicate_function_definition_fails(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            eval_fake(BASE+"1000 T main_00000000(nx::CPU&)\n", "")

if __name__ == "__main__":
    unittest.main()
