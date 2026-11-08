"""Synthetic nm audits: no ROM, copyrighted AOT objects or proprietary tables."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.boot_runtime_link_gate import (
    inspect, PROVIDERS, PROPRIETARY_MODULES, VIDEOOUT_IMPORTS
)

def listing(items, ty):
    return "".join(f"{i*16:x} {ty} {sym}\n" for i,sym in enumerate(sorted(items),1))

COMPLETE = listing(PROVIDERS, "T")
UNDEFINED = listing(PROPRIETARY_MODULES | VIDEOOUT_IMPORTS, "U")

class BootLinkTest(unittest.TestCase):
    def test_complete_public_boot_and_remaining_real_aot_requirements(self):
        r=inspect(COMPLETE,UNDEFINED)
        self.assertEqual(r["status"],"PASS")
        self.assertFalse(r["strict_executable_link_passed"])
        self.assertFalse(r["aot_tables_linked"])

    def test_missing_provider_fails(self):
        r=inspect(listing(set(PROVIDERS)-{"nx::boot()"},"T"),UNDEFINED)
        self.assertEqual(r["status"],"FAIL")
        self.assertIn("nx::boot()",r["missing_or_duplicated_providers"])

    def test_unresolved_provider_fails(self):
        r=inspect(COMPLETE,UNDEFINED + " U nx::plat::reserve(unsigned long, unsigned long)\n")
        self.assertEqual(r["status"],"FAIL")

    def test_proprietary_tables_cannot_be_fake_satisfied(self):
        r=inspect(COMPLETE + "1000 D nx_module_main\n",UNDEFINED.replace("U nx_module_main\n",""))
        self.assertEqual(r["status"],"FAIL")
        self.assertIn("nx_module_main",r["proprietary_module_definitions_forbidden"])

    def test_missing_real_sce_videoout_import_fails(self):
        r=inspect(COMPLETE,listing(set(PROPRIETARY_MODULES)|{"sceVideoOutOpen"},"U"))
        self.assertEqual(r["status"],"FAIL")
        self.assertEqual(len(r["missing_real_videoout_imports"]),2)

if __name__=="__main__":
    unittest.main()
