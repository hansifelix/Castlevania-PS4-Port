"""Synthetic ELF nm checks; no proprietary shader, Switch object, or GPU binary."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.link.ps4_nvn_vulkan_closure import inspect, REQUIRED

def nm(names, kind):
    return "".join(f"{i+1:016x} {kind} {n}\\n" for i,n in enumerate(sorted(names)))

ALL = set(REQUIRED) | {
    "nx::plat::vulkan_create_surface(void*, void*, unsigned long*, void*)",
    "nx::nvn::gpu_present(unsigned long, int const*)",
    "nx::nvn::gpu_submit()",
}
# Signature of gpu_submit need not match this synthetic fixture precisely;
# the partial-link gate uses an unambiguous function prefix.
IMPORT = " U vkGetInstanceProcAddr\\n"

class VulkanBridgeTest(unittest.TestCase):
    def test_real_core_and_import_partially_close(self):
        x=inspect(nm(ALL,"T"), IMPORT)
        self.assertEqual(x["status"],"PASS_PARTIAL")
        self.assertFalse(x["strict_gpu_link"])
        self.assertFalse(x["ps4_frame_presented"])
    def test_no_vulkan_import_cannot_claim_real_backend(self):
        x=inspect(nm(ALL,"T"), "")
        self.assertEqual(x["status"],"FAIL")
    def test_fabricated_internal_vulkan_loader_cannot_pass(self):
        x=inspect(nm(ALL|{"vkGetInstanceProcAddr"},"T"),IMPORT)
        self.assertEqual(x["status"],"FAIL")
    def test_missing_gpu_submit_fails(self):
        x=inspect(nm(ALL-{"nx::nvn::gpu_submit()"},"T"),IMPORT)
        self.assertEqual(x["status"],"FAIL")
        self.assertIn("nx::nvn::gpu_submit(",x["missing_or_ambiguous_providers"])
    def test_missing_platform_bridge_fails(self):
        x=inspect(nm(ALL-{"nx::plat::vulkan_get_instance_proc_addr()"},"T"),IMPORT)
        self.assertEqual(x["status"],"FAIL")
    def test_duplicate_providers_fail(self):
        txt=nm(ALL,"T") + "0000 T nx::plat::ps4::vk_get_instance_proc_addr()\\n"
        x=inspect(txt,IMPORT)
        self.assertEqual(x["status"],"FAIL")

if __name__=="__main__":
    unittest.main()
