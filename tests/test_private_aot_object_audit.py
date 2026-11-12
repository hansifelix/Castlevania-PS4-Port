import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.etapa90.audit_private_aot_objects import (
    EXPECTED,
    audit,
    elf64_rel_x86_64,
    module_for,
    safe_report_destination,
)


def elf_header(entry=0):
    data = bytearray(64)
    data[:4] = b"\x7fELF"
    data[4:7] = bytes([2, 1, 1])
    struct.pack_into("<HHI", data, 16, 1, 62, 1)
    struct.pack_into("<Q", data, 24, entry)
    struct.pack_into("<H", data, 52, 64)
    return bytes(data)


class PrivateAotObjectAuditTests(unittest.TestCase):
    def test_accepts_only_elf64_relocatable_x86_64(self):
        ok, reason = elf64_rel_x86_64(elf_header())
        self.assertTrue(ok)
        self.assertEqual(reason, "ELF64_ET_REL_x86_64")

        bad = bytearray(elf_header())
        struct.pack_into("<H", bad, 16, 2)
        self.assertEqual(elf64_rel_x86_64(bytes(bad)), (False, "not_ET_REL"))

        bad = bytearray(elf_header())
        struct.pack_into("<H", bad, 18, 183)
        self.assertEqual(elf64_rel_x86_64(bytes(bad)), (False, "not_x86_64"))

    def test_resolves_module_names_from_folders_and_backup_archives(self):
        self.assertEqual(module_for(("Kazuma_Traducoes_AOT_Privado", "MAIN")), "main")
        self.assertEqual(module_for(("main_backup_02.zip",)), "main")
        self.assertEqual(module_for(("SDK-objects.zip",)), "sdk")
        self.assertEqual(module_for(("subsdk0.zip",)), "subsdk0")
        self.assertIsNone(module_for(("unclassified.zip",)))

    def test_complete_archive_passes_structure_elf_and_manifest_without_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            root.mkdir()
            archive_path = root / "aot_backup.zip"
            manifest = {}
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for module, count in EXPECTED.items():
                    width = 4 if module == "main" else 3
                    for index in range(count):
                        name = f"{module}/code_{index:0{width}d}.o"
                        blob = elf_header(entry=index)
                        archive.writestr(name, blob)
                        manifest[name] = hashlib.sha256(blob).hexdigest()
                archive.writestr("manifests/manifest.json", json.dumps(manifest))

            before = archive_path.read_bytes()
            report = audit(root)
            after = archive_path.read_bytes()

            self.assertEqual(before, after)
            self.assertEqual(report["overall_status"], "PASS_STRUCTURE_ELF_AND_MANIFESTS")
            self.assertTrue(report["object_index_coverage_complete"])
            self.assertTrue(report["all_object_copies_are_elf64_et_rel_x86_64"])
            self.assertTrue(report["manifest_hash_coverage_complete"])
            self.assertEqual(report["totals"]["expected_unique_object_indices"], 1916)
            self.assertEqual(report["totals"]["object_copies_found"], 1916)
            self.assertTrue(report["inputs_modified"] is False)
            self.assertTrue(report["files_extracted"] is False)
            self.assertTrue(report["compilation_performed"] is False)
            self.assertTrue(report["link_performed"] is False)

    def test_identical_backup_replicas_are_not_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blob = elf_header()
            for backup in ("main_backup_1.zip", "main_backup_2.zip"):
                with zipfile.ZipFile(root / backup, "w") as archive:
                    archive.writestr("code_0000.o", blob)
            report = audit(root)
            main = report["module_results"]["main"]
            self.assertEqual(main["same_hash_backup_replicas"], 1)
            self.assertEqual(main["conflicting_hash_indices"], [])

    def test_different_hashes_for_same_index_are_reported_as_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for backup, entry in (("main_backup_1.zip", 1), ("main_backup_2.zip", 2)):
                with zipfile.ZipFile(root / backup, "w") as archive:
                    archive.writestr("code_0000.o", elf_header(entry=entry))
            report = audit(root)
            conflicts = report["module_results"]["main"]["conflicting_hash_indices"]
            self.assertEqual(len(conflicts), 1)
            self.assertEqual(conflicts[0]["index"], 0)

    def test_report_must_be_outside_private_input_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            root.mkdir()
            with self.assertRaises(ValueError):
                safe_report_destination(root, root / "report.json")


if __name__ == "__main__":
    unittest.main()
