"""Synthetic, storage-safe regression of the actual strict-link invocation."""
from pathlib import Path
import os
import sys
import tempfile
from types import SimpleNamespace
from unittest import mock
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.link.strict_link_no_storage import build_command, summary, run


class StrictDisklessLink(unittest.TestCase):
    def make_sdk(self, root: Path):
        sdk = root / "sdk"
        (sdk / "lib").mkdir(parents=True)
        (sdk / "link.x").write_text("SECTIONS {}\n")
        (sdk / "lib" / "crt1.o").write_bytes(b"fixture")
        (sdk / "lib" / "libm.a").write_bytes(b"fixture")
        obj = root / "private-aot.o"
        obj.write_bytes(b"synthetic ELF placeholder, not actual commercial content")
        return sdk, obj

    def test_linker_output_is_always_devnull_not_gigabyte_elf(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            sdk,obj=self.make_sdk(root)
            cmd=build_command(sdk,[obj],linker="ld.lld-18")
            self.assertEqual(cmd[cmd.index("-o")+1],os.devnull)
            self.assertIn("--no-undefined",cmd)
            self.assertIn("-pie",cmd)
            self.assertIn("--fatal-warnings",cmd)
            self.assertEqual(cmd.count(str(obj)),1)
            self.assertIn("-lc++",cmd)
            self.assertIn("-lkernel",cmd)
            self.assertIn("-lm",cmd)
            self.assertFalse(any(x.endswith(".pkg") for x in cmd))

    def test_strict_link_failure_keeps_diagnostics_but_no_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            sdk,obj=self.make_sdk(root)
            proc=SimpleNamespace(returncode=1, stderr=(
                "ld.lld-18: error: undefined symbol: nx::plat::real_gpu\n"
                "ld.lld-18: error: undefined symbol: nx::plat::real_gpu\n"
                "ld.lld-18: error: unable to find library -lVulkan\n"))
            with mock.patch("tools.link.strict_link_no_storage.subprocess.run",return_value=proc) as call:
                result=run(sdk,[obj],"ld.lld-18",90)
            self.assertEqual(result["status"],"BLOCKED")
            self.assertEqual(result["undefined_symbols_reported"],1)
            self.assertEqual(result["missing_libraries_reported"],1)
            self.assertFalse(result["elf_output_saved"])
            self.assertFalse(result["game_boot_verified"])
            self.assertEqual(result["drive_bytes_written"],0)
            self.assertEqual(call.call_args.args[0][call.call_args.args[0].index("-o")+1],os.devnull)
            self.assertFalse(any(p.name=="result.elf" for p in root.iterdir()))

    def test_success_still_not_a_validated_elf_or_ps4_boot(self):
        report=summary(0,"",12,2)
        self.assertEqual(report["status"],"PASS_DRYRUN")
        self.assertFalse(report["elf_format_verified"])
        self.assertFalse(report["eboot_created"])
        self.assertFalse(report["pkg_created"])

    def test_invalid_inputs_fail_closed_without_invoking_linker(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            sdk,obj=self.make_sdk(root)
            for objs in ([],[root/"absent.o"]):
                with self.assertRaises(ValueError):
                    build_command(sdk,objs)
            with self.assertRaises(ValueError):
                build_command(sdk,[obj],linker="ld.lld -o myfile")
            with self.assertRaises(ValueError):
                build_command(sdk,[obj],error_limit=0)
            (sdk/"link.x").unlink()
            with self.assertRaises(ValueError):
                build_command(sdk,[obj])


if __name__=="__main__":
    unittest.main()
