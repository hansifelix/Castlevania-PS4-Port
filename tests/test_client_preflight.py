"""Synthetic-only tests; never download or execute game files."""
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.honkai.client_preflight import inspect


class ClientPreflightTests(unittest.TestCase):
    def test_android_apk_arm64_unity(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test.apk"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("AndroidManifest.xml", b"synthetic")
                z.writestr("classes.dex", b"synthetic")
                z.writestr("lib/arm64-v8a/libunity.so", b"synthetic")
                z.writestr("lib/arm64-v8a/libil2cpp.so", b"synthetic")
            result = inspect(path)
            self.assertEqual(result["format"], "android_apk")
            self.assertEqual(result["architecture"], "arm64-v8a")
            self.assertTrue(result["android_evidence"]["has_unity_native_library"])
            self.assertTrue(result["android_evidence"]["has_il2cpp_native_library"])
            self.assertFalse(result["signature_verified"])
            self.assertFalse(result["executes_game"])

    def test_pe_windows_x64(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic.exe"
            blob = bytearray(256)
            blob[:2] = b"MZ"
            struct.pack_into("<I", blob, 0x3C, 0x80)
            blob[0x80:0x84] = b"PE\x00\x00"
            struct.pack_into("<H", blob, 0x84, 0x8664)
            path.write_bytes(blob)
            result = inspect(path, compute_hash=True)
            self.assertEqual(result["format"], "windows_pe")
            self.assertEqual(result["architecture"], "x86_64")
            self.assertEqual(len(result["sha256"]), 64)
            self.assertEqual(result["ps4_compatible"], "not_tested")

    def test_elf_arm64(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic.so"
            blob = bytearray(64)
            blob[:4] = b"\x7fELF"
            blob[4:6] = b"\x02\x01"
            struct.pack_into("<H", blob, 18, 183)
            path.write_bytes(blob)
            result = inspect(path)
            self.assertEqual(result["format"], "elf")
            self.assertEqual(result["architecture"], "arm64/64")

    def test_unknown_and_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "random.bin"
            path.write_bytes(b"abc")
            self.assertEqual(inspect(path)["format"], "unknown")
            link = Path(td) / "alias.bin"
            link.symlink_to(path)
            with self.assertRaises(ValueError):
                inspect(link)

    def test_zip_not_fake_apk(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "not_apk.apk"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("lib/arm64-v8a/libunity.so", b"x")
            result = inspect(path)
            self.assertEqual(result["format"], "zip_other")


if __name__ == "__main__":
    unittest.main()
