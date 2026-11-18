import hashlib
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from tools.link.export_public_runtime_symbol_hashes import (
    AuditError,
    build_manifest,
    inspect_object_root,
)


class RuntimeHashExporterTests(unittest.TestCase):
    def make_root(self, root):
        root.mkdir()
        for name in ("RT-a.o", "GAME-meta.o", "PS4-pad.o"):
            (root / name).write_bytes(name.encode("ascii"))

    def fake_runner(self, args, **kwargs):
        path = Path(args[-1])
        if path.name == "RT-a.o":
            out = f"{path}: _Zsynthetic T 00000000 4\n{path}: _Zduplicate T 00000004 4\n"
        elif path.name == "GAME-meta.o":
            out = f"{path}: _Zduplicate T 00000000 4\n"
        else:
            out = f"{path}: _Zsynthetic D 00000000 8\n"
        return CompletedProcess(args, 0, out, "")

    def test_manifest_is_hash_only_and_tracks_duplicate_definitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "objects"
            self.make_root(root)
            with patch("tools.link.export_public_runtime_symbol_hashes.shutil.which", return_value="/usr/bin/llvm-nm-18"):
                manifest = build_manifest(
                    root, runner=self.fake_runner,
                    expected_runtime=1, expected_game=1, expected_platform=1,
                )
            self.assertEqual(manifest["object_count"], 3)
            self.assertEqual(manifest["runtime_translation_units"], 1)
            self.assertEqual(manifest["game_metadata_translation_units"], 1)
            self.assertEqual(manifest["ps4_platform_adapter_units"], 1)
            by_hash = {row["sha256"]: row for row in manifest["symbol_hashes"]}
            synthetic = hashlib.sha256(b"_Zsynthetic").hexdigest()
            duplicate = hashlib.sha256(b"_Zduplicate").hexdigest()
            self.assertEqual(by_hash[synthetic]["definition_count"], 2)
            self.assertEqual(by_hash[synthetic]["object_count"], 2)
            self.assertEqual(by_hash[synthetic]["kinds"], ["D", "T"])
            self.assertEqual(by_hash[duplicate]["definition_count"], 2)
            self.assertEqual(by_hash[duplicate]["object_count"], 2)
            self.assertNotIn("_Zsynthetic", str(manifest))
            self.assertNotIn("_Zduplicate", str(manifest))
            self.assertNotIn("RT-a.o", str(manifest))
            self.assertFalse(manifest["symbol_names_included"])
            self.assertFalse(manifest["provider_paths_included"])
            self.assertFalse(manifest["private_aot_data_included"])

    def test_manifest_hash_is_canonical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "objects"
            self.make_root(root)
            with patch("tools.link.export_public_runtime_symbol_hashes.shutil.which", return_value="/usr/bin/llvm-nm-18"):
                manifest = build_manifest(
                    root, runner=self.fake_runner,
                    expected_runtime=1, expected_game=1, expected_platform=1,
                )
            canonical = "".join(
                f'{row["sha256"]}:{row["definition_count"]}:{row["object_count"]}:{",".join(row["kinds"])}\n'
                for row in manifest["symbol_hashes"]
            )
            self.assertEqual(
                hashlib.sha256(canonical.encode("ascii")).hexdigest(),
                manifest["symbol_hash_manifest_sha256"],
            )

    def test_wrong_object_count_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "objects"
            self.make_root(root)
            with self.assertRaisesRegex(AuditError, "RUNTIME_OBJECT_COUNT_MISMATCH"):
                inspect_object_root(root, expected_runtime=2, expected_game=1, expected_platform=1)

    def test_symlink_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "objects"
            self.make_root(root)
            target = root / "RT-a.o"
            target.unlink()
            (root / "RT-a.o").symlink_to(root / "GAME-meta.o")
            with self.assertRaisesRegex(AuditError, "OBJECT_ROOT_CONTAINS_SYMLINK"):
                inspect_object_root(root, expected_runtime=1, expected_game=1, expected_platform=1)

    def test_nm_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "objects"
            self.make_root(root)
            def bad_runner(args, **kwargs):
                return CompletedProcess(args, 1, "", "private diagnostic")
            with patch("tools.link.export_public_runtime_symbol_hashes.shutil.which", return_value="/usr/bin/llvm-nm-18"):
                with self.assertRaisesRegex(AuditError, "NM_PROVIDER_SCAN_FAILED"):
                    build_manifest(
                        root, runner=bad_runner,
                        expected_runtime=1, expected_game=1, expected_platform=1,
                    )

    def test_malformed_nm_output_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "objects"
            self.make_root(root)
            def bad_runner(args, **kwargs):
                return CompletedProcess(args, 0, "this is not nm output\n", "")
            with patch("tools.link.export_public_runtime_symbol_hashes.shutil.which", return_value="/usr/bin/llvm-nm-18"):
                with self.assertRaisesRegex(AuditError, "NM_OUTPUT_UNRECOGNIZED"):
                    build_manifest(
                        root, runner=bad_runner,
                        expected_runtime=1, expected_game=1, expected_platform=1,
                    )


if __name__ == "__main__":
    unittest.main()
