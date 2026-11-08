"""Synthetic nm audits: no ROM, copyrighted AOT objects or proprietary tables."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.boot_runtime_link_gate import (
    inspect, PROVIDERS, KERNEL_PROVIDERS, HORIZON_SERVICE_PROVIDERS, FILE_IO_PROVIDERS, THREAD_CLOCK_PROVIDERS, THREAD_LAUNCH_PROVIDERS, APP0_PROVIDERS, SAVEDATA_PROVIDERS, SAVEDATA_IMPORTS, PROPRIETARY_MODULES, VIDEOOUT_IMPORTS
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

    def test_genuine_kernel_symbols_required_only_on_expanded_gate(self):
        from tools.link.boot_runtime_link_gate import KERNEL_PROVIDERS
        r = inspect(COMPLETE, UNDEFINED, require_kernel=True)
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual(set(r["missing_or_duplicated_providers"]), KERNEL_PROVIDERS)
        r = inspect(listing(PROVIDERS | KERNEL_PROVIDERS, "T"), UNDEFINED,
                    require_kernel=True)
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["required_public_provider_count"],
                         len(PROVIDERS | KERNEL_PROVIDERS))
        self.assertTrue(r["kernel_providers_required"])

    def test_horizon_services_must_be_real_when_requested(self):
        baseline = listing(PROVIDERS | KERNEL_PROVIDERS, "T")
        unresolved = UNDEFINED + listing(HORIZON_SERVICE_PROVIDERS, "U")
        result = inspect(baseline, unresolved, require_kernel=True, require_services=True)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(set(result["missing_or_duplicated_providers"]), HORIZON_SERVICE_PROVIDERS)
        complete = listing(PROVIDERS | KERNEL_PROVIDERS | HORIZON_SERVICE_PROVIDERS, "T")
        result = inspect(complete, UNDEFINED, require_kernel=True, require_services=True)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["horizon_services_defined"], 7)
        self.assertTrue(result["horizon_services_required"])
        self.assertFalse(result["strict_executable_link_passed"])

    def test_false_service_definition_cannot_hide_unresolved_reference(self):
        complete = listing(PROVIDERS | KERNEL_PROVIDERS | HORIZON_SERVICE_PROVIDERS, "T")
        one = sorted(HORIZON_SERVICE_PROVIDERS)[0]
        result = inspect(complete, UNDEFINED + " U " + one + "\n", require_kernel=True, require_services=True)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn(one, result["public_providers_still_undefined"])

    def test_real_posix_fs_providers_required_only_for_new_link(self):
        base = listing(PROVIDERS | KERNEL_PROVIDERS | HORIZON_SERVICE_PROVIDERS, "T")
        r = inspect(base, UNDEFINED, require_file_io=True)
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual(set(r["missing_or_duplicated_providers"]), FILE_IO_PROVIDERS)
        r = inspect(base + listing(FILE_IO_PROVIDERS, "T"), UNDEFINED,
                    require_file_io=True)
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["file_io_providers_defined"], 5)
        self.assertFalse(r["strict_executable_link_passed"])
        missing = sorted(FILE_IO_PROVIDERS)[0]
        r = inspect(base + listing(FILE_IO_PROVIDERS, "T"), UNDEFINED + " U " + missing + "\n",
                    require_file_io=True)
        self.assertEqual(r["status"], "FAIL")
        self.assertIn(missing, r["public_providers_still_undefined"])

    def test_clock_and_thread_providers_are_real(self):
        from tools.link.boot_runtime_link_gate import THREAD_CLOCK_PROVIDERS
        base = listing(PROVIDERS, "T")
        r = inspect(base, UNDEFINED, require_clock_thread=True)
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual(set(r["missing_or_duplicated_providers"]), THREAD_CLOCK_PROVIDERS)
        complete = listing(PROVIDERS | THREAD_CLOCK_PROVIDERS, "T")
        r = inspect(complete, UNDEFINED, require_clock_thread=True)
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["clock_thread_providers_defined"], 4)
        r = inspect(complete, UNDEFINED + " U nx::plat::sleep_ns(long)\n",
                    require_clock_thread=True)
        self.assertEqual(r["status"], "FAIL")
        self.assertIn("nx::plat::sleep_ns(long)", r["public_providers_still_undefined"])

    def test_native_thread_launch_requires_all_three_providers(self):
        complete = listing(PROVIDERS | THREAD_LAUNCH_PROVIDERS, "T")
        missing = inspect(COMPLETE, UNDEFINED, require_thread_launch=True)
        self.assertEqual(missing["status"], "FAIL")
        self.assertEqual(set(missing["missing_or_duplicated_providers"]), THREAD_LAUNCH_PROVIDERS)
        good = inspect(complete, UNDEFINED, require_thread_launch=True)
        self.assertEqual(good["status"], "PASS")
        self.assertEqual(good["thread_launch_providers_defined"], 3)
        self.assertFalse(good["strict_executable_link_passed"])
        one = sorted(THREAD_LAUNCH_PROVIDERS)[0]
        unresolved = inspect(complete, UNDEFINED + " U " + one + "\n",
                             require_thread_launch=True)
        self.assertEqual(unresolved["status"], "FAIL")
        self.assertIn(one, unresolved["public_providers_still_undefined"])

    def test_real_app0_config_providers_required_only_for_new_link(self):
        defined = listing(PROVIDERS | APP0_PROVIDERS, "T")
        missing = inspect(COMPLETE, UNDEFINED, require_app0=True)
        self.assertEqual(missing["status"], "FAIL")
        self.assertEqual(set(missing["missing_or_duplicated_providers"]), APP0_PROVIDERS)
        r = inspect(defined, UNDEFINED, require_app0=True)
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["app0_providers_defined"], 3)
        self.assertFalse(r["aot_tables_linked"])
        one = sorted(APP0_PROVIDERS)[0]
        undefined = inspect(defined, UNDEFINED + " U " + one + "\n",
                            require_app0=True)
        self.assertEqual(undefined["status"], "FAIL")
        self.assertIn(one, undefined["public_providers_still_undefined"])

    def test_sony_savedata_mount_is_a_real_provider(self):
        base=listing(PROVIDERS | SAVEDATA_PROVIDERS,"T")
        imports=UNDEFINED + listing(SAVEDATA_IMPORTS,"U")
        result=inspect(COMPLETE,imports,require_savedata=True)
        self.assertEqual(result["status"],"FAIL")
        self.assertIn("nx::plat::writable_root()",result["missing_or_duplicated_providers"])
        result=inspect(base,imports,require_savedata=True)
        self.assertEqual(result["status"],"PASS")
        self.assertEqual(result["missing_real_savedata_imports"],[])
        self.assertFalse(result["strict_executable_link_passed"])
        result=inspect(base,UNDEFINED,require_savedata=True)
        self.assertEqual(result["status"],"FAIL")
        self.assertEqual(set(result["missing_real_savedata_imports"]),SAVEDATA_IMPORTS)

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
