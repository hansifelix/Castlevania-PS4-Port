import io
import struct
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.etapa90.private_aot_symbol_inventory import (
    audit, build_provider_candidates, parse_elf_symbols,
    summarize_duplicate_definitions, summarize_provider_candidates,
)


def tiny_elf64(comdat=False):
    strings = b"\0_defined_fn\0_missing_fn\0"
    names = {"_defined_fn": 1, "_missing_fn": 13}
    symbols = b"".join([
        bytes(24),
        struct.pack("<IBBHQQ", names["_defined_fn"], 0x12, 0, 4, 0, 1),
        struct.pack("<IBBHQQ", names["_missing_fn"], 0x12, 0, 0, 0, 0),
    ])
    shstr = b"\0.strtab\0.symtab\0.shstrtab\0.text\0.group\0"
    shnames = {name: shstr.index(name.encode()) for name in (".strtab", ".symtab", ".shstrtab", ".text", ".group")}
    section_count = 6 if comdat else 5
    shoff = 64
    data_off = shoff + section_count * 64
    str_off = data_off
    sym_off = str_off + len(strings)
    shstr_off = sym_off + len(symbols)
    text_off = shstr_off + len(shstr)
    group_data = struct.pack("<II", 1, 4) if comdat else b""
    group_off = text_off + 1
    sections = [
        bytes(64),
        struct.pack("<IIQQQQIIQQ", shnames[".strtab"], 3, 0, 0, str_off, len(strings), 0, 0, 1, 0),
        struct.pack("<IIQQQQIIQQ", shnames[".symtab"], 2, 0, 0, sym_off, len(symbols), 1, 1, 8, 24),
        struct.pack("<IIQQQQIIQQ", shnames[".shstrtab"], 3, 0, 0, shstr_off, len(shstr), 0, 0, 1, 0),
        struct.pack("<IIQQQQIIQQ", shnames[".text"], 1, 6, 0, text_off, 1, 0, 0, 1, 0),
    ]
    if comdat:
        sections.append(struct.pack(
            "<IIQQQQIIQQ", shnames[".group"], 17, 0, 0, group_off,
            len(group_data), 2, 1, 4, 4
        ))
    ident = b"\x7fELF" + bytes([2, 1, 1]) + bytes(9)
    header = struct.pack(
        "<16sHHIQQQIHHHHHH", ident, 1, 62, 1, 0, 0, shoff, 0, 64, 0, 0,
        64, section_count, 3
    )
    return header + b"".join(sections) + strings + symbols + shstr + b"\xc3" + group_data

class PrivateAotSymbolInventoryTests(unittest.TestCase):
    def test_reads_global_defined_and_undefined_symbols_by_exact_name(self):
        result = parse_elf_symbols(tiny_elf64())
        self.assertIn("_defined_fn", result["defined"])
        self.assertIn("_missing_fn", result["undefined"])
        self.assertEqual(result["external_symbol_entries"], 2)

    def test_parses_binding_type_visibility_and_comdat_membership(self):
        ordinary = parse_elf_symbols(tiny_elf64())
        detail = ordinary["defined_details"]["_defined_fn"][0]
        self.assertEqual(detail["binding"], "GLOBAL")
        self.assertEqual(detail["type"], "FUNC")
        self.assertEqual(detail["visibility"], "DEFAULT")
        self.assertFalse(detail["comdat"])

        grouped = parse_elf_symbols(tiny_elf64(comdat=True))
        self.assertTrue(grouped["defined_details"]["_defined_fn"][0]["comdat"])

    def test_summarizes_duplicate_definition_binding_and_comdat_profiles(self):
        global_func = {
            "binding": "GLOBAL", "type": "FUNC", "visibility": "DEFAULT",
            "section_index": 4, "comdat": True,
        }
        weak_func = {
            "binding": "WEAK", "type": "FUNC", "visibility": "DEFAULT",
            "section_index": 4, "comdat": True,
        }
        strong_non_comdat = {
            "binding": "GLOBAL", "type": "FUNC", "visibility": "DEFAULT",
            "section_index": 5, "comdat": False,
        }
        profiles, totals = summarize_duplicate_definitions(
            {"_duplicated": ["MAIN:0", "SDK:4", "subsdk0:2"]},
            {"_duplicated": {
                "MAIN:0": [global_func],
                "SDK:4": [weak_func],
                "subsdk0:2": [strong_non_comdat],
            }},
        )
        self.assertEqual(profiles["_duplicated"]["location_count"], 3)
        self.assertFalse(profiles["_duplicated"]["all_locations_comdat"])
        self.assertEqual(profiles["_duplicated"]["non_comdat_global_modules"], ["subsdk0"])
        self.assertEqual(totals["duplicate_definition_symbol_names"], 1)
        self.assertEqual(totals["duplicate_definition_locations_with_comdat"], 2)
        self.assertEqual(totals["duplicate_definition_locations_without_comdat"], 1)
        self.assertEqual(totals["duplicate_definition_binding_entry_counts"], {"GLOBAL": 2, "WEAK": 1})

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

    def test_summarizes_provider_candidates_per_consumer_object_symbol_pair(self):
        result = summarize_provider_candidates({
            "_single_provider": {
                "MAIN:3": ["MAIN:1"],
                "SDK:2": ["SDK:4"],
            },
            "_multiple_providers": {
                "MAIN:8": ["MAIN:4", "SDK:9"],
            },
        })
        self.assertEqual(result["undefined_consumer_object_symbol_pairs_with_aot_provider_candidates"], 3)
        self.assertEqual(result["undefined_consumer_object_symbol_pairs_with_single_provider_candidate"], 2)
        self.assertEqual(result["undefined_consumer_object_symbol_pairs_with_multiple_provider_candidates"], 1)
        self.assertEqual(result["undefined_consumer_object_symbol_pairs_with_cross_module_provider_candidates"], 1)
        self.assertEqual(result["max_aot_provider_candidates_per_consumer_object_symbol_pair"], 2)

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
            duplicate = result["duplicate_definition_profiles"]["_defined_fn"]
            self.assertEqual(duplicate["location_count"], 2)
            self.assertEqual(result["totals"]["duplicate_definition_binding_entry_counts"], {"GLOBAL": 2})
            self.assertEqual(result["totals"]["duplicate_definition_type_entry_counts"], {"FUNC": 2})
            self.assertEqual(result["totals"]["duplicate_definition_visibility_entry_counts"], {"DEFAULT": 2})
            self.assertEqual(result["totals"]["duplicate_definition_locations_without_comdat"], 2)
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
