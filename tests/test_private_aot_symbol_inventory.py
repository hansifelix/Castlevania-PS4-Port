import io
import struct
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.etapa90.private_aot_symbol_inventory import audit, build_provider_candidates, parse_elf_symbols


def tiny_elf64():
    strings = b"\0_defined_fn\0_missing_fn\0"
    names = {"_defined_fn": 1, "_missing_fn": 13}
    symbols = b"".join([
        bytes(24),
        struct.pack("<IBBHQQ", names["_defined_fn"], 0x10, 0, 1, 0, 0),
        struct.pack("<IBBHQQ", names["_missing_fn"], 0x10, 0, 0, 0, 0),
    ])
    shstr = b"\0.strtab\0.symtab\0.shstrtab\0"
    shnames = {".strtab": 1, ".symtab": 9, ".shstrtab": 17}
    shoff = 64
    str_off = shoff + 4 * 64
    sym_off = str_off + len(strings)
    shstr_off = sym_off + len(symbols)
    sections = [
        bytes(64),
        struct.pack("<IIQQQQIIQQ", shnames[".strtab"], 3, 0, 0, str_off, len(strings), 0, 0, 1, 0),
        struct.pack("<IIQQQQIIQQ", shnames[".symtab"], 2, 0, 0, sym_off, len(symbols), 1, 0, 8, 24),
        struct.pack("<IIQQQQIIQQ", shnames[".shstrtab"], 3, 0, 0, shstr_off, len(shstr), 0, 0, 1, 0),
    ]
    ident = b"\x7fELF" + bytes([2, 1, 1]) + bytes(9)
    header = struct.pack("<16sHHIQQQIHHHHHH", ident, 1, 62, 1, 0, 0, shoff, 0, 64, 0, 0, 64, 4, 3)
    return header + b"".join(sections) + strings + symbols + shstr


class PrivateAotSymbolInventoryTests(unittest.TestCase):
    def test_reads_global_defined_and_undefined_symbols_by_exact_name(self):
        result = parse_elf_symbols(tiny_elf64())
        self.assertIn("_defined_fn", result["defined"])
        self.assertIn("_missing_fn", result["undefined"])
        self.assertEqual(result["external_symbol_entries"], 2)

    def test_maps_undefined_symbols_to_other_objects_including_same_module(self):
        definitions = {
            "_shared_fn": ["MAIN:4", "SDK:8"],
            "_same_module_fn": ["MAIN:9"],
        }
        undefined = {
            "_shared_fn": {"MAIN:5", "subsdk0:2"},
            "_same_module_fn": {"MAIN:10"},
        }
        result = build_provider_candidates(definitions, undefined)
        self.assertEqual(result["_shared_fn"]["MAIN:5"], ["MAIN:4", "SDK:8"])
        self.assertEqual(result["_shared_fn"]["subsdk0:2"], ["MAIN:4", "SDK:8"])
        self.assertEqual(result["_same_module_fn"]["MAIN:10"], ["MAIN:9"])

    def test_audits_zip_and_tar_gz_members_without_extracting(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "private"
            root.mkdir()
            elf = tiny_elf64()

            with zipfile.ZipFile(root / "KazumaMAIN.zip", "w") as archive:
                archive.writestr("objects/code_0000.o", elf)

            tar_path = root / "KazumaSDK.tar.gz"
            with tarfile.open(tar_path, "w:gz") as archive:
                info = tarfile.TarInfo("objects/code_0000.o")
                info.size = len(elf)
                archive.addfile(info, io.BytesIO(elf))

            result = audit(root)
            self.assertEqual(result["module_results"]["main"]["object_copies_parsed"], 1)
            self.assertEqual(result["module_results"]["sdk"]["object_copies_parsed"], 1)
            self.assertFalse(result["files_extracted"])
            self.assertEqual(sorted(p.name for p in root.iterdir()), ["KazumaMAIN.zip", "KazumaSDK.tar.gz"])

    def test_rejects_non_relocatable_elf(self):
        blob = bytearray(tiny_elf64())
        struct.pack_into("<H", blob, 16, 2)
        with self.assertRaisesRegex(ValueError, "not_elf64_et_rel_x86_64"):
            parse_elf_symbols(bytes(blob))

    def test_rejects_truncated_section_table(self):
        with self.assertRaisesRegex(ValueError, "truncated_elf_header"):
            parse_elf_symbols(b"\x7fELF")


if __name__ == "__main__":
    unittest.main()
