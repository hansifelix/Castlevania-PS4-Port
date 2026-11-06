"""Fixtures públicos da Etapa 81; nenhuma instrução do jogo."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.etapa81.aot_report_gate import parse_report


class CoverageTest(unittest.TestCase):
    def test_subsdk0_complete(self):
        r = parse_report("functions 14173, handled 902188, unhandled 0\n")
        self.assertTrue(r["all_instructions_supported"])
        self.assertEqual(r["functions_detected"], 14173)
        self.assertFalse(r["ready_for_ps4_link"])

    def test_sdk_has_unhandled_stg(self):
        r = parse_report("functions 40112, handled 1654429, unhandled 1\n\n       1 stg\n")
        self.assertFalse(r["all_instructions_supported"])
        self.assertEqual(r["instructions_unhandled"], 1)
        self.assertEqual(r["unhandled_mnemonics"], [{"quantidade": 1, "mnemonico": "stg"}])

    def test_invalid_report_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_report("Finished!")

    def test_empty_report_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_report("")

    def test_inconsistent_report_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_report("functions 10, handled 2, unhandled 0")

    def test_extra_text_not_classified(self):
        r = parse_report("functions 3, handled 3, unhandled 0\nuser note stg\n")
        self.assertEqual(r["unhandled_mnemonics"], [])


if __name__ == "__main__":
    unittest.main()
