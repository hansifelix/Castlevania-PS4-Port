"""Etapa 78 — dados NSO sintéticos, sem jogo."""
from pathlib import Path
import hashlib
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.etapa78.exefs_linkage_probe import inspect_exefs, inspect_module

MODULES = ("main", "sdk", "subsdk0")


def make_nso(path, imported, exported, reloc=257, weak=False):
    image = bytearray(0x300)
    struct.pack_into("<I", image, 4, 0x20)
    image[0x20:0x24] = b"MOD0"
    struct.pack_into("<i", image, 0x24, 0x60)
    entries = [(6, 0x100), (5, 0x148), (11, 24), (7, 0x180), (8, 24), (0, 0)]
    for i, pair in enumerate(entries):
        struct.pack_into("<qQ", image, 0x80 + i * 16, *pair)
    strings = b"\x00" + imported.encode() + b"\x00" + exported.encode() + b"\x00"
    image[0x148:0x148 + len(strings)] = strings
    struct.pack_into("<IBBHQQ", image, 0x118, 1, 0x20 if weak else 0x10, 0, 0, 0, 0)
    struct.pack_into("<IBBHQQ", image, 0x130, 2 + len(imported), 0, 0, 1, 0, 0)
    struct.pack_into("<QQq", image, 0x180, 0x200, reloc, 0)
    header = bytearray(0x100)
    header[:4] = b"NSO0"
    struct.pack_into("<III", header, 0x10, 0x100, 0, len(image))
    path.write_bytes(header + image)


class ExefsLinkageTest(unittest.TestCase):
    def setup_files(self, root):
        make_nso(root / "main", "foo", "bar")
        make_nso(root / "sdk", "bar", "foo")
        make_nso(root / "subsdk0", "external", "quux", weak=True)

    def test_valid_cross_module_linkage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.setup_files(root)
            result = inspect_exefs(root)
            self.assertEqual(result["unique_imports"], 3)
            self.assertEqual(result["imports_resolved_in_exefs"], 2)
            self.assertEqual(result["imports_without_exefs_definition"], 1)
            self.assertEqual(result["imports_without_exefs_definition_nonweak"], 0)
            self.assertEqual(result["linkage"]["subsdk0"]["unresolved_weak_imports"], 1)
            self.assertFalse(result["aot_generated"])
            self.assertFalse(result["unresolved_names_exported"])

    def test_external_strong_import_is_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.setup_files(root)
            make_nso(root / "subsdk0", "external", "quux", weak=False)
            result = inspect_exefs(root)
            self.assertEqual(result["imports_without_exefs_definition_nonweak"], 1)
            self.assertEqual(result["linkage"]["subsdk0"]["unresolved_weak_imports"], 0)

    def test_rela_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "main"
            make_nso(path, "foo", "bar")
            info, _, _, _ = inspect_module(path)
            self.assertEqual(info["rela_entries"], 1)
            self.assertEqual(info["relocation_types"], {"ABS64": 1})
            self.assertEqual(info["dynamic_symbols"], 3)

    def test_detect_unknown_relocation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "main"
            make_nso(path, "foo", "bar", reloc=9999)
            info, _, _, _ = inspect_module(path)
            self.assertEqual(info["unknown_relocation_types"], ["9999"])

    def test_wrong_sha_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "main"
            make_nso(path, "foo", "bar")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                inspect_module(path, {"build_id": "00" * 32, "nso_sha256_reference": "ff" * 32})

    def test_missing_nso_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                inspect_module(Path(directory) / "missing")

    def test_invalid_dynamic_table(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "main"
            make_nso(path, "foo", "bar")
            data = bytearray(path.read_bytes())
            struct.pack_into("<i", data, 0x100 + 0x24, 0x999999)
            path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "dynamic"):
                inspect_module(path)

    def test_no_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            make_nso(path / "main", "foo", "bar")
            (path / "sdk").symlink_to(path / "main")
            with self.assertRaisesRegex(ValueError, "simbólico"):
                inspect_module(path / "sdk")


if __name__ == "__main__":
    unittest.main()
