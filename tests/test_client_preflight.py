"""Synthetic-only tests; never download or execute game files."""
import hashlib
import stat
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


    def test_elf_header_agrees_with_android_abi(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "realistic.apk"
            arm64 = bytearray(64)
            arm64[:4] = b"\x7fELF"
            arm64[4:6] = b"\x02\x01"  # ELF64, little-endian
            struct.pack_into("<H", arm64, 18, 183)  # AArch64
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("AndroidManifest.xml", b"synthetic")
                z.writestr("lib/arm64-v8a/libunity.so", arm64)
            evidence = inspect(path)["android_evidence"]
            self.assertEqual(evidence["native_header_checked"], 1)
            self.assertEqual(evidence["native_header_matching"], 1)
            self.assertEqual(evidence["native_header_mismatch"], 0)
            self.assertTrue(evidence["native_library_abi_consistent"])

    def test_mislabelled_native_library_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "mislabelled.apk"
            arm64 = bytearray(64)
            arm64[:4] = b"\x7fELF"
            arm64[4:6] = b"\x02\x01"
            struct.pack_into("<H", arm64, 18, 183)
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("AndroidManifest.xml", b"synthetic")
                z.writestr("lib/x86_64/libunity.so", arm64)
            evidence = inspect(path)["android_evidence"]
            self.assertEqual(evidence["native_header_mismatch"], 1)
            self.assertFalse(evidence["native_library_abi_consistent"])

    def test_fake_native_library_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "fake.apk"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("AndroidManifest.xml", b"synthetic")
                z.writestr("lib/arm64-v8a/libil2cpp.so", b"not ELF")
            evidence = inspect(path)["android_evidence"]
            self.assertEqual(evidence["native_header_invalid"], 1)
            self.assertFalse(evidence["native_library_abi_consistent"])

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


    def test_rejects_duplicate_zip_member_names(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "dupes.apk"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("AndroidManifest.xml", b"ok")
                # Duplicate entries are ambiguous even when Python can read them.
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    z.writestr("AndroidManifest.xml", b"evil")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                inspect(path)

    def test_rejects_traversal_and_backslash_paths(self):
        with tempfile.TemporaryDirectory() as td:
            for bad in ("../data.txt", "res/../evil.txt", r"res\\evil.txt", "/absolute"):
                path = Path(td) / "bad.apk"
                with zipfile.ZipFile(path, "w") as z:
                    z.writestr("AndroidManifest.xml", b"synthetic")
                    z.writestr(bad, b"unsafe")
                with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "unsafe path"):
                    inspect(path)

    def test_rejects_zip_bomb_like_ratio(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "compressed.apk"
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_LZMA) as z:
                z.writestr("AndroidManifest.xml", b"synthetic")
                z.writestr("payload", b"\x00" * 4_000_000)
            with self.assertRaisesRegex(ValueError, "compression ratio"):
                inspect(path)

    def test_rejects_symlink_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "symlink.apk"
            link = zipfile.ZipInfo("link")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("AndroidManifest.xml", b"synthetic")
                z.writestr(link, b"etc/passwd")
            with self.assertRaisesRegex(ValueError, "symlink"):
                inspect(path)

    def test_reference_hash_must_match_trusted_value(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "unknown.exe"
            path.write_bytes(b"file bytes not executable")
            expected = hashlib.sha256(path.read_bytes()).hexdigest()
            result = inspect(path, expected_sha256=expected.upper())
            self.assertTrue(result["reference_hash_matches"])
            self.assertEqual(result["sha256"], expected)
            self.assertEqual(result["malware_free"], "not_evaluated")
            with self.assertRaisesRegex(ValueError, "mismatch"):
                inspect(path, expected_sha256="0" * 64)
            with self.assertRaisesRegex(ValueError, "64 hexadecimal"):
                inspect(path, expected_sha256="invalid")

    def test_zip_not_fake_apk(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "not_apk.apk"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("lib/arm64-v8a/libunity.so", b"x")
            result = inspect(path)
            self.assertEqual(result["format"], "zip_other")


if __name__ == "__main__":
    unittest.main()
