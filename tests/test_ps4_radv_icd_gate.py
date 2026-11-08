"""Fail-closed synthetic symbol scenarios for the real PS4 RADV archive gate."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.link.ps4_vkloader_icd_gate import REQUIRED
from tools.link.ps4_radv_icd_gate import inspect, RADV_PROVIDERS

PRESENT = REQUIRED | RADV_PROVIDERS | {
    "nx::plat::vulkan_create_surface(void*, void*, unsigned long*, void*)",
    "nx::nvn::gpu_submit(std::__1::vector<foo> const&)",
    "nx::nvn::gpu_present(unsigned long, int const*)",
}


def nm(symbols, kind):
    if kind == "U":
        return "".join(" U " + n + "\n" for n in sorted(symbols))
    return "".join(f"{i + 100:016x} {kind} {n}\n"
                   for i,n in enumerate(sorted(symbols)))


class RadvPartialLinkGate(unittest.TestCase):
    def test_real_archive_closure_requires_three_icd_symbols(self):
        r=inspect(nm(PRESENT,"T"),nm({"sceVideoOutOpen", "malloc"}, "U"))
        self.assertEqual(r["status"],"PASS_PARTIAL_RADV")
        self.assertEqual(r["radv_icd_entries_defined"],3)
        self.assertFalse(r["strict_executable_link_passed"])
        self.assertFalse(r["nvn_frame_presented_on_ps4"])
        self.assertFalse(r["eboot_or_pkg_created"])

    def test_old_undefined_icd_must_fail(self):
        src=PRESENT-{"vk_icdGetInstanceProcAddr"}
        r=inspect(nm(src,"T"),nm({"vk_icdGetInstanceProcAddr"},"U"))
        self.assertEqual(r["status"],"FAIL")

    def test_missing_any_icd_provider_fails(self):
        for provider in RADV_PROVIDERS:
            r=inspect(nm(PRESENT-{provider},"T"),"")
            self.assertEqual(r["status"],"FAIL")
            self.assertIn(provider,r["missing_or_duplicated_real_providers"])

    def test_multiple_icd_definitions_fail(self):
        src=nm(PRESENT,"T") + "000000000001abcd T vk_icdGetInstanceProcAddr\n"
        r=inspect(src,"")
        self.assertEqual(r["status"],"FAIL")

    def test_missing_nvn_present_fails(self):
        r=inspect(nm({x for x in PRESENT if not x.startswith("nx::nvn::gpu_present(")},"T"),"")
        self.assertEqual(r["status"],"FAIL")

    def test_unresolved_vulkan_frontend_fails(self):
        r=inspect(nm(PRESENT,"T"),nm({"vkGetInstanceProcAddr"},"U"))
        self.assertEqual(r["status"],"FAIL")

    def test_bad_nm_record_is_not_success(self):
        with self.assertRaises(ValueError):
            inspect("invalid symbol record","")


if __name__=="__main__":
    unittest.main()
