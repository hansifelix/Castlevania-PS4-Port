"""Synthetic tests for candidate provider audit; no commercial game data."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.etapa90.symbol_providers import analyze, parse_nm, category

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "etapa90" / "symbol_providers.py"


class TestSymbolProviders(unittest.TestCase):
    def test_parse_nm_undefined_and_defined_global_only(self):
        need = parse_nm(" U ceil\n                 U _ZN2nx4callEv\n0000 T main\n", undefined=True)
        self.assertEqual(need, {"ceil", "_ZN2nx4callEv"})
        defs = parse_nm("0000 T ceil\n0001 t hidden\n0002 W _ZN2nx4callEv\n0003 U missing\n", undefined=False)
        self.assertEqual(defs, {"ceil", "_ZN2nx4callEv"})

    def test_six_original_undefined_refs_and_real_provider_candidates(self):
        source = {"nx::call(nx::CPU&, unsigned long)",
                  "nx::unimpl(nx::CPU&, unsigned long, char const*)",
                  "ceil", "floor", "fma", "trunc"}
        loader = {"nx::call(nx::CPU&, unsigned long)",
                  "nx::unimpl(nx::CPU&, unsigned long, char const*)"}
        result = analyze(source, {"public_loader": loader, "libm": {"ceil", "floor", "fma"}})
        self.assertEqual(result["required"], 6)
        self.assertEqual(result["candidate_matched"], 5)
        self.assertEqual(result["missing"], 1)
        self.assertEqual([x["symbol"] for x in result["symbols"] if x["status"] == "missing"], ["trunc"])
        self.assertFalse(result["strict_link_verified"])

    def test_requires_exact_symbol_name_and_version(self):
        r = analyze({"symbol@VER_1", "_ZN2nx4callEv"}, {"wrong": {"symbol", "_ZN2nx4callEi"}})
        self.assertEqual(r["missing"], 2)

    def test_no_providers_cannot_be_green(self):
        r = analyze({"ceil"}, {})
        self.assertEqual((r["required"], r["candidate_matched"], r["missing"]), (1, 0, 1))

    def test_multiple_candidates_and_categories(self):
        r = analyze({"ceil", "_ZN2nx3fooEv", "__cxa_atexit"},
                    {"p1": {"ceil", "__cxa_atexit"}, "p2": {"ceil", "_ZN2nx3fooEv"}})
        self.assertEqual(r["missing"], 0)
        self.assertEqual(next(x for x in r["symbols"] if x["symbol"] == "ceil")["candidate_providers"], ["p1", "p2"])
        self.assertEqual(category("__cxa_atexit"), "cxx_abi")
        self.assertEqual(category("_ZN2nx3fooEv"), "nx_runtime")

    def test_bad_record_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Invalid nm record"):
            parse_nm("an arbitrary bad result", undefined=True)

    def test_cli_missing_symbols_exit_2_and_no_providers(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)
            (path / "need.nm").write_text("                 U ceil\n                 U trunc\n", encoding="utf8")
            (path / "provided.nm").write_text("00000 T ceil\n", encoding="utf8")
            out = path / "out.json"
            result = subprocess.run([sys.executable, str(SCRIPT),
                "--undefined", str(path / "need.nm"),
                "--defined", f"libm={path / 'provided.nm'}",
                "--json", str(out),
                "--fail-on-missing"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("missing=1", result.stdout)
            self.assertIn('"strict_link_verified": false', out.read_text())

    def test_cli_full_candidates_do_not_mean_final_link(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)
            (path / "need.nm").write_text(" U ceil\n", encoding="utf8")
            (path / "libm.nm").write_text("0000 T ceil\n", encoding="utf8")
            result = subprocess.run([sys.executable, str(SCRIPT),
                "--undefined", str(path / "need.nm"),
                "--defined", f"libm={path / 'libm.nm'}",
                "--fail-on-missing"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("strict_link_verified=NO", result.stdout)


if __name__ == "__main__":
    unittest.main()
