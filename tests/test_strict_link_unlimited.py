"""Tests for unlimited strict-link diagnostics while retaining /dev/null output."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.strict_link_unlimited import run_unlimited


class UnlimitedStrictLink(unittest.TestCase):
    def make_sdk(self, root: Path):
        sdk = root / "sdk"
        (sdk / "lib").mkdir(parents=True)
        (sdk / "link.x").write_text("SECTIONS {}\n")
        (sdk / "lib" / "crt1.o").write_bytes(b"fixture")
        (sdk / "lib" / "libm.a").write_bytes(b"fixture")
        obj = root / "gpu-slice.o"
        obj.write_bytes(b"synthetic ELF placeholder")
        return sdk, obj

    def test_all_undefined_symbols_are_reported_and_output_stays_devnull(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sdk, obj = self.make_sdk(root)
            stderr = (
                "ld.lld: error: undefined symbol: nx::nvn::ReplayScope::ReplayScope(unsigned long)\n"
                "ld.lld: error: undefined symbol: sceVideoOutOpen\n"
                "ld.lld: error: undefined symbol: nx::nvn::ReplayScope::ReplayScope(unsigned long)\n"
            )
            proc = SimpleNamespace(returncode=1, stderr=stderr)
            with mock.patch("tools.link.strict_link_unlimited.subprocess.run",
                            return_value=proc) as call:
                report = run_unlimited(
                    sdk, [obj], linker="ld.lld-18", timeout=90,
                    extra_libs=["SceGnmDriver"],
                )
            command = call.call_args.args[0]
            self.assertIn("--error-limit=0", command)
            self.assertNotIn("--error-limit=100", command)
            self.assertEqual(command[command.index("-o") + 1], os.devnull)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertEqual(report["linker_error_limit"], 0)
            self.assertFalse(report["log_may_be_truncated_by_linker"])
            self.assertFalse(report["full_diagnostic_list_truncated"])
            self.assertEqual(
                report["all_undefined_symbols"],
                ["nx::nvn::ReplayScope::ReplayScope(unsigned long)", "sceVideoOutOpen"],
            )
            self.assertFalse(report["elf_output_saved"])
            self.assertFalse(report["eboot_created"])
            self.assertFalse(report["pkg_created"])
            self.assertEqual(report["drive_bytes_written"], 0)

    def test_missing_sdk_input_fails_before_running_linker(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sdk, obj = self.make_sdk(root)
            (sdk / "link.x").unlink()
            with self.assertRaises(ValueError):
                run_unlimited(sdk, [obj])


if __name__ == "__main__":
    unittest.main()
