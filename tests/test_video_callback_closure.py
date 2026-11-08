"""Synthetic llvm-nm inputs; no proprietary game assets."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.video_callback_closure import (
    REQUIRED_CALLBACKS, REQUIRED_PROVIDERS, inspect,
)

def symbol_lines(symbols, tag="T"):
    return "".join(f"{i * 8:016x} {tag} {s}\n" for i, s in enumerate(sorted(symbols), 1))

DEFINITIONS = symbol_lines(REQUIRED_CALLBACKS | REQUIRED_PROVIDERS)

class ClosureTests(unittest.TestCase):
    def test_all_13_hooks_and_provider_link(self):
        r = inspect(DEFINITIONS, "                 U nx::call(nx::CPU&, unsigned long)\n")
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["defined_callbacks"], 13)
        self.assertFalse(r["final_executable_link"])

    def test_missing_callback_is_failure(self):
        hooks = set(REQUIRED_CALLBACKS)
        hooks.remove(next(iter(hooks)))
        r = inspect(symbol_lines(hooks | REQUIRED_PROVIDERS), "")
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual(len(r["missing_callbacks"]), 1)

    def test_duplicate_callback_is_failure(self):
        r = inspect(DEFINITIONS + "0000 T " + sorted(REQUIRED_CALLBACKS)[0] + "\n", "")
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual(len(r["duplicate_callbacks"]), 1)

    def test_unresolved_internal_symbol_is_failure(self):
        r = inspect(DEFINITIONS, "   U " + sorted(REQUIRED_CALLBACKS)[0] + "\n")
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual(len(r["unresolved_internal_callbacks_or_providers"]), 1)

    def test_missing_video_provider_is_failure(self):
        p = set(REQUIRED_PROVIDERS)
        p.remove(next(iter(p)))
        r = inspect(symbol_lines(set(REQUIRED_CALLBACKS) | p), "")
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual(len(r["missing_or_duplicate_providers"]), 1)

    def test_full_ps4_videoout_stack_requires_real_os_imports(self):
        defs = DEFINITIONS + "abc0 T nx::game::after_init()\nabc8 T nx::plat::screen_size(unsigned int&, unsigned int&)\n"
        imports = "".join("   U "+name+"\n" for name in
            ("sceVideoOutOpen", "sceVideoOutGetResolutionStatus", "sceVideoOutClose"))
        result = inspect(defs, imports, include_videoout=True)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["videoout_stack_verified"])
        self.assertFalse(result["final_executable_link"])
        result = inspect(defs, "", include_videoout=True)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(len(result["missing_real_sce_videoout_imports"]), 3)
        result = inspect(DEFINITIONS, imports, include_videoout=True)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(len(result["missing_videoout_providers"]), 2)
        result = inspect(defs, imports + "  U nx::plat::screen_size(unsigned int&, unsigned int&)\n",
                         include_videoout=True)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(len(result["unresolved_videoout_providers"]), 1)

    def test_unexpected_stub_name_is_failure(self):
        r = inspect(DEFINITIONS + "abcd T nx_castlevania_fake_stub(nx::CPU&)\n", "")
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual(len(r["unexpected_callbacks"]), 1)


if __name__ == "__main__":
    unittest.main()
