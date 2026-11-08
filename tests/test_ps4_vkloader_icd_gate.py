"""Small immutable tests for real vkloader -> RADV symbol transition."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.ps4_vkloader_icd_gate import REQUIRED, ICD_ENTRY, inspect

EXTRA = {
    "nx::plat::vulkan_create_surface(void*, void*, unsigned long*, void*)",
    "nx::nvn::gpu_submit(std::__1::vector<int> const&)",
    "nx::nvn::gpu_present(unsigned long, int const*)",
}
def nm(symbols, kind):
    if kind=="U":
        return "".join(f"                 U {s}\n" for s in sorted(symbols))
    return "".join(f"{i+42:016x} {kind} {s}\n" for i,s in enumerate(sorted(symbols)))

class RealVkloaderGate(unittest.TestCase):
    def setUp(self):
        self.defined = nm(REQUIRED | EXTRA, "T")
        self.undefined = nm({ICD_ENTRY, "sceKernelDebugOutText"}, "U")

    def test_genuine_import_chain_passes_as_partial_only(self):
        r=inspect(self.defined, self.undefined)
        self.assertEqual(r["status"], "PASS_PARTIAL_VKLOADER_TO_ICD")
        self.assertTrue(r["actual_vkloader_frontend_defined"])
        self.assertTrue(r["real_radv_icd_import_unresolved"])
        self.assertFalse(r["strict_executable_link"])
        self.assertFalse(r["mesa_radv_archive_linked"])
        self.assertFalse(r["ps4_frame_visible"])
        self.assertEqual(r["google_drive_bytes_written"], 0)

    def test_genuine_frontend_missing_fails(self):
        r=inspect(nm((REQUIRED-{"vkGetInstanceProcAddr"})|EXTRA,"T"),
                  self.undefined + nm({"vkGetInstanceProcAddr"},"U"))
        self.assertEqual(r["status"], "FAIL")
        self.assertIn("vkGetInstanceProcAddr", r["bad_or_missing_provider_names"])

    def test_fake_icd_definition_fails(self):
        r=inspect(self.defined + nm({ICD_ENTRY},"T"), self.undefined)
        self.assertEqual(r["status"], "FAIL")

    def test_missing_real_radv_reference_fails(self):
        r=inspect(self.defined, nm({"sceKernelDebugOutText"},"U"))
        self.assertEqual(r["status"], "FAIL")

    def test_duplicate_vkloader_definition_fails(self):
        r=inspect(self.defined + nm({"vkGetInstanceProcAddr"},"T"),self.undefined)
        self.assertEqual(r["status"], "FAIL")

    def test_missing_nvn_submit_fails(self):
        defs=(REQUIRED | EXTRA) - {next(x for x in EXTRA if x.startswith("nx::nvn::gpu_submit("))}
        r=inspect(nm(defs,"T"),self.undefined)
        self.assertEqual(r["status"], "FAIL")
        self.assertIn("nx::nvn::gpu_submit(",r["bad_or_missing_provider_names"])

    def test_malformed_nm_is_not_a_pass(self):
        with self.assertRaises(ValueError):
            inspect("not actually nm output", self.undefined)

if __name__=="__main__":
    unittest.main()
