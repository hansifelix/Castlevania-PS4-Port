import hashlib
import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path

from tools.etapa96.export_openorbis_symbol_hashes import (
    AuditError,
    build_symbol_hash_manifest,
    collect_provider_files,
    extract_openorbis_lib,
    sha256_file,
)


def make_archive(path: Path, members):
    with tarfile.open(path, "w:gz") as archive:
        for name, payload in members:
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))


def fake_nm(path: Path, mode="ok"):
    source = f"""#!/usr/bin/env python3
import sys
path = sys.argv[-1]
mode = {mode!r}
if mode == "fail":
    raise SystemExit(1)
if mode == "malformed":
    print("not an nm posix record")
else:
    print(f"{{path}}[one.o]: _ZfakeA T 00000000 4")
    print(f"{{path}}[two.o]: _ZfakeA T 00000000 4")
    print(f"{{path}}[two.o]: _ZfakeB W 00000000 4")
"""
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)
    return path


class OpenOrbisHashExportTests(unittest.TestCase):
    def test_export_contains_only_hashes_and_preserves_archive_ambiguity(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            archive = base / "toolchain.tar.gz"
            make_archive(archive, [("lib/libexample.a", b"synthetic archive bytes")])
            digest = sha256_file(archive)
            root = base / "lib"
            self.assertEqual(extract_openorbis_lib(archive, root), 1)
            nm = fake_nm(base / "fake-nm")
            report = build_symbol_hash_manifest(root, str(nm), digest)

            hashes = {row["sha256"]: row for row in report["symbol_hashes"]}
            fake_a = hashlib.sha256(b"_ZfakeA").hexdigest()
            fake_b = hashlib.sha256(b"_ZfakeB").hexdigest()
            self.assertEqual(hashes[fake_a]["definition_count"], 2)
            self.assertEqual(hashes[fake_a]["kinds"], ["T"])
            self.assertEqual(hashes[fake_b]["definition_count"], 1)
            self.assertEqual(hashes[fake_b]["kinds"], ["W"])
            self.assertTrue(report["scan_complete"])
            self.assertFalse(report["symbol_names_included"])
            self.assertFalse(report["provider_paths_included"])
            serialized = json.dumps(report)
            self.assertNotIn("_ZfakeA", serialized)
            self.assertNotIn("_ZfakeB", serialized)
            self.assertNotIn(str(root), serialized)
            self.assertNotIn("libexample.a", serialized)

    def test_archive_hash_mismatch_is_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            archive = base / "toolchain.tar.gz"
            make_archive(archive, [("lib/libexample.a", b"x")])
            with self.assertRaisesRegex(AuditError, "SDK_ARCHIVE_SHA256_MISMATCH"):
                extract_openorbis_lib(archive, base / "lib", expected_sha256="0" * 64)

    def test_tar_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            archive = base / "toolchain.tar.gz"
            make_archive(archive, [("lib/../../escape.a", b"x")])
            with self.assertRaisesRegex(AuditError, "SDK_ARCHIVE_UNSAFE_PATH"):
                extract_openorbis_lib(archive, base / "lib")

    def test_symlink_escape_in_sdk_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            archive = base / "toolchain.tar.gz"
            with tarfile.open(archive, "w:gz") as bundle:
                info = tarfile.TarInfo("lib/escape.so")
                info.type = tarfile.SYMTYPE
                info.linkname = "../../outside.so"
                bundle.addfile(info)
            with self.assertRaisesRegex(AuditError, "SDK_LIB_LINK_ESCAPES_ROOT"):
                extract_openorbis_lib(archive, base / "lib")

    def test_internal_symlink_alias_is_resolved_once(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "lib"
            root.mkdir()
            target = root / "libtarget.so.1"
            target.write_bytes(b"synthetic")
            (root / "libtarget.so").symlink_to(target.name)
            files, aliases = collect_provider_files(root)
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0], target.resolve())
            self.assertEqual(aliases, 1)

    def test_external_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "lib"
            root.mkdir()
            outside = base / "outside.so"
            outside.write_bytes(b"not inside sdk")
            (root / "alias.so").symlink_to(outside)
            with self.assertRaisesRegex(AuditError, "SDK_LIB_SYMLINK_ESCAPES_ROOT"):
                collect_provider_files(root)

    def test_nm_failure_and_malformed_output_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "lib"
            root.mkdir()
            (root / "libexample.a").write_bytes(b"synthetic")
            archive_sha = "a" * 64
            with self.assertRaisesRegex(AuditError, "NM_PROVIDER_SCAN_FAILED"):
                build_symbol_hash_manifest(root, str(fake_nm(base / "nm-fail", "fail")), archive_sha)
            with self.assertRaisesRegex(AuditError, "NM_OUTPUT_UNRECOGNIZED"):
                build_symbol_hash_manifest(root, str(fake_nm(base / "nm-bad", "malformed")), archive_sha)

    def test_empty_provider_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "lib"
            root.mkdir()
            with self.assertRaisesRegex(AuditError, "SDK_LIB_NO_PROVIDER_FILES"):
                build_symbol_hash_manifest(root, "nm", "a" * 64)


if __name__ == "__main__":
    unittest.main()
