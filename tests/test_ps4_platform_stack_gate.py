import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.ps4_platform_stack_gate import (
    PRIVATE_AOT,
    REAL_IMPORTS,
    REQUIRED,
    inspect,
)


def listing(names, kind):
    return "\n".join(f"00000000 {kind} {name}" for name in sorted(names)) + "\n"


class PS4PlatformStackGateTests(unittest.TestCase):
    def fixture(self):
        defined = set(REQUIRED)
        undefined = set(PRIVATE_AOT) | set(REAL_IMPORTS)
        return defined, undefined

    def test_public_stack_passes_only_when_all_real_providers_are_defined(self):
        defined, undefined = self.fixture()
        report = inspect(listing(defined, "T"), listing(undefined, "U"))
        self.assertEqual(report["status"], "PASS_PUBLIC_STACK_AOT_PENDING")
        self.assertEqual(report["private_aot_modules_still_unresolved"], sorted(PRIVATE_AOT))
        self.assertFalse(report["strict_executable_link_passed"])
        self.assertFalse(report["eboot_created"])
        self.assertFalse(report["pkg_created"])

    def test_missing_provider_fails_closed(self):
        defined, undefined = self.fixture()
        defined.remove("nx::plat::audio_open(void (*)(void*))")
        report = inspect(listing(defined, "T"), listing(undefined, "U"))
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            "nx::plat::audio_open(void (*)(void*))",
            report["public_providers_missing_or_duplicated"],
        )

    def test_provider_still_undefined_fails_closed(self):
        defined, undefined = self.fixture()
        undefined.add("nx::plat::read_pad(nx::plat::PadState&)")
        report = inspect(listing(defined, "T"), listing(undefined, "U"))
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            "nx::plat::read_pad(nx::plat::PadState&)",
            report["public_providers_still_undefined"],
        )

    def test_private_aot_must_remain_unresolved_and_never_be_faked(self):
        defined, undefined = self.fixture()
        defined.add("nx_module_main")
        report = inspect(listing(defined, "T"), listing(undefined, "U"))
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("nx_module_main", report["private_aot_module_definitions_forbidden"])

    def test_required_real_sdk_imports_must_remain_visible(self):
        defined, undefined = self.fixture()
        undefined.remove("sceVideoOutOpen")
        report = inspect(listing(defined, "T"), listing(undefined, "U"))
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("sceVideoOutOpen", report["required_real_sdk_imports_missing"])


if __name__ == "__main__":
    unittest.main()
