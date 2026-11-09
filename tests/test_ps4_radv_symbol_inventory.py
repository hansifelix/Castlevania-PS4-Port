"""Synthetic inventory tests for unresolved symbols from the public RADV slice."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.ps4_radv_symbol_inventory import inspect


def nm(kind: str, name: str) -> str:
    return f"                 {kind} {name}\\n"


class RadvSymbolInventory(unittest.TestCase):
    def test_public_runtime_sdk_driver_and_toolchain_categories(self):
        text = "".join([
            nm("U", "nx::game::kInfo"),
            nm("U", "nx::nvn::ReplayScope::ReplayScope(unsigned long)"),
            nm("U", "nx::plat::monotonic_ns()"),
            nm("U", "nx::memory_init()"),
            nm("U", "sceVideoOutOpen"),
            nm("U", "vkCreateInstance"),
            nm("U", "vk_icdGetInstanceProcAddr"),
            nm("U", "radv_CreateDevice"),
            nm("U", "std::__1::basic_string<char>::size()"),
            nm("U", "__cxa_throw"),
            nm("U", "malloc"),
            nm("U", "mystery_external_symbol"),
        ])
        report = inspect(text)
        counts = {row["category"]: row["distinct"] for row in report["categories"]}
        self.assertEqual(counts["NX_GAME"], 1)
        self.assertEqual(counts["NX_NVN"], 1)
        self.assertEqual(counts["NX_PLATFORM"], 1)
        self.assertEqual(counts["NX_OTHER"], 1)
        self.assertEqual(counts["SCE_SDK"], 1)
        self.assertEqual(counts["VULKAN_API"], 2)
        self.assertEqual(counts["MESA_RADV"], 1)
        self.assertEqual(counts["CXX_ABI"], 2)
        self.assertEqual(counts["C_LIBC_POSIX"], 1)
        self.assertEqual(counts["OTHER_EXTERNAL"], 1)
        self.assertEqual(report["classification"], "INVENTORY_ONLY_NOT_RESOLUTION")

    def test_duplicate_symbols_are_counted_once_and_strong_wins(self):
        report = inspect(nm("w", "optional_weak") + nm("U", "required_strong") +
                         nm("U", "required_strong"))
        self.assertEqual(report["total_undefined_distinct"], 2)
        self.assertEqual(report["strong_undefined_distinct"], 1)
        self.assertEqual(report["weak_undefined_distinct"], 1)

    def test_malformed_or_defined_records_fail_closed(self):
        for bad in ("not an nm line", " T defined_symbol"):
            with self.assertRaises(ValueError):
                inspect(bad)

    def test_inventory_never_claims_runtime_or_package_success(self):
        report = inspect(nm("U", "nx::game::kInfo"))
        self.assertFalse(report["eboot_created"])
        self.assertFalse(report["pkg_created"])
        self.assertFalse(report["ps4_vulkan_executed"])
        self.assertFalse(report["wsi_videoout_executed"])
        self.assertFalse(report["game_boot_verified"])
        self.assertEqual(report["drive_bytes_written"], 0)


if __name__ == "__main__":
    unittest.main()
