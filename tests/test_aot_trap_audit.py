"""Etapa 82: teste apenas sobre fontes C++ sintéticos."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.etapa82.aot_trap_audit import audit_cpp


class TrapAuditTests(unittest.TestCase):
    def test_udf_and_undecodable_even_when_upstream_says_zero(self):
        with tempfile.TemporaryDirectory() as root:
            d = Path(root)
            (d / "code_000.cpp").write_text(
                'void f() {\n'
                ' nx::unimpl(c, NXB + 0x20ull, "udf");\n'
                ' nx::unimpl(c, NXB + 0x24ull, "undecodable 0xabcd");\n'
                '}\n', encoding="utf-8")
            r = audit_cpp(d, 1)
            self.assertEqual(r["nx_unimpl_calls"], 2)
            self.assertEqual(r["categories"], {"udf": 1, "undecodable": 1})
            self.assertEqual(r["samples_metadata_only"][0]["deslocamento_guest_hex"], "0x20")
            self.assertIsNone(r["all_paths_reachable"])

    def test_no_traps_is_only_static_evidence(self):
        with tempfile.TemporaryDirectory() as root:
            d = Path(root)
            (d / "code_003.cpp").write_text("void f() { c.x[0] = 1; }", encoding="utf-8")
            r = audit_cpp(d)
            self.assertTrue(r["no_unimpl_calls_detected"])
            self.assertFalse(r["linked_ps4"])
            self.assertFalse(r["game_boot_ps4"])

    def test_multiline_and_other(self):
        with tempfile.TemporaryDirectory() as root:
            d = Path(root)
            (d / "code_000.cpp").write_text(
                'nx::unimpl(\n c, NXB + 0xa0ull,\n "stg"\n);\n', encoding="utf-8")
            r = audit_cpp(d)
            self.assertEqual(r["categories"], {"other": 1})

    def test_exception_default_guard_and_stg(self):
        with tempfile.TemporaryDirectory() as root:
            d = Path(root)
            (d / "code_132.cpp").write_text(
                'default: nx::unimpl(c, lp_, "destino de excepción sin generar");\n'
                'nx::unimpl(c, NXB + 0x62a7f0ull, "stg x8, [x8]");\n',
                encoding="utf-8",
            )
            r = audit_cpp(d, 1)
            self.assertEqual(r["categories"],
                             {"exception_default_guard": 1, "stg": 1})

    def test_expected_count_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            d = Path(root)
            (d / "code_000.cpp").write_text("void f() {}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Quantidade"):
                audit_cpp(d, 73)

    def test_no_files_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "Quantidade"):
                audit_cpp(Path(root))

    def test_link_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            d = Path(root)
            (d / "code_000.cpp").write_text("void f() {}", encoding="utf-8")
            (d / "code_001.cpp").symlink_to(d / "code_000.cpp")
            with self.assertRaisesRegex(ValueError, "regular"):
                audit_cpp(d)


if __name__ == "__main__":
    unittest.main()
