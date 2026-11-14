import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.etapa90.private_aot_sdk_provider_audit import (
    complete,
    parse_nm,
    parse_nm_records,
    provider_files,
    safe_report,
    scan,
)


def inventory():
    return {
        "audit_mode": "READ_ONLY_SYMBOL_TABLE_PARSE_NO_EXTRACT_NO_COMPILE_NO_LINK",
        "root_name": "synthetic-private",
        "index_coverage_complete": True,
        "duplicate_metadata_complete": True,
        "invalid_objects": [],
        "private_symbol_names_in_report": True,
        "files_extracted": False,
        "compilation_performed": False,
        "link_performed": False,
        "totals": {
            "object_copies_parsed": 3,
            "undefined_symbols_without_provider_in_aot_inventory": 4,
        },
        "undefined_without_aot_provider": {
            "_ZprivateA": ["main:1"],
            "_ZprivateB": ["sdk:2"],
            "_ZprivateUnique": ["main:3"],
            "external_missing": ["subsdk0:4"],
        },
    }


class ProviderAuditTests(unittest.TestCase):
    def test_requires_complete_inventory(self):
        data = inventory()
        data["index_coverage_complete"] = False
        self.assertFalse(complete(data))
        data = inventory()
        del data["invalid_objects"]
        self.assertFalse(complete(data))

    def test_parses_nm_archive_and_object_rows(self):
        got = parse_nm_records(
            "libx.a[a.o]: _ZprivateA T 0 8\n"
            "libx.a[a.o]: external U 0 0\n"
            "object.o: _ZprivateB W 10 4\n"
        )
        self.assertEqual(
            got,
            [
                ("libx.a[a.o]", "_ZprivateA", "T"),
                ("object.o", "_ZprivateB", "W"),
            ],
        )
        self.assertEqual(
            parse_nm("libx.a[a.o]: _ZprivateA T 0 8\n"),
            [("_ZprivateA", "T")],
        )

    def test_rejects_unrecognized_nm_output(self):
        with self.assertRaisesRegex(ValueError, "unrecognized_nm_posix_line"):
            parse_nm_records("not nm output")
        with self.assertRaisesRegex(ValueError, "unrecognized_nm_posix_line"):
            parse_nm_records("nm: unexpected partial-output diagnostic")

    def test_real_gnu_nm_archive_member_format(self):
        nm = shutil.which("nm")
        compiler = shutil.which("cc")
        archiver = shutil.which("ar")
        if not (nm and compiler and archiver):
            self.skipTest("GNU nm, C compiler, or ar unavailable")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "provider.c"
            obj = root / "provider.o"
            archive = root / "libproviders.a"
            source.write_text(
                "int provider_symbol(void) { return 7; }\\n",
                encoding="utf-8",
            )
            subprocess.run(
                [compiler, "-c", str(source), "-o", str(obj)],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [archiver, "rcs", str(archive), str(obj)],
                check=True,
                capture_output=True,
                text=True,
            )
            result = subprocess.run(
                [nm, "-A", "-g", "--defined-only", "--format=posix", str(archive)],
                check=True,
                capture_output=True,
                text=True,
            )
            records = parse_nm_records(result.stdout)
            self.assertTrue(
                any(
                    origin.endswith("[provider.o]")
                    and symbol == "provider_symbol"
                    and kind.upper() == "T"
                    for origin, symbol, kind in records
                ),
                result.stdout,
            )

    def test_rejects_warning_even_when_nm_output_is_present(self):
        with self.assertRaisesRegex(ValueError, "nm_warning_in_output"):
            parse_nm_records(
                "warning: partial archive read\n"
                "libx.a[a.o]: _ZprivateA T 0 8\n"
            )

    def test_archive_member_duplicates_are_ambiguous(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ("one.a", "two.a", "none.a"):
                (root / name).write_bytes(b"synthetic")

            def fake(cmd, **kwargs):
                path = cmd[-1]
                name = Path(path).name
                rows = {
                    "one.a": (
                        f"{path}[x.o]: _ZprivateUnique T 0 8\n"
                        f"{path}[x.o]: _ZprivateB W 0 8\n"
                        f"{path}[x.o]: _ZprivateA T 0 8\n"
                        f"{path}[y.o]: _ZprivateA T 0 8\n"
                    ),
                    "two.a": f"{path}[z.o]: _ZprivateB T 0 8\n",
                    "none.a": f"{path}[n.o]: unrelated T 0 8\n",
                }[name]
                return SimpleNamespace(returncode=0, stdout=rows, stderr="")

            with patch(
                "tools.etapa90.private_aot_sdk_provider_audit.subprocess.run",
                side_effect=fake,
            ):
                result = scan(inventory(), [("sdk", root)], "fake-nm")

            self.assertEqual(result["exact_provider_candidate_count"], 1)
            self.assertEqual(result["ambiguous_provider_candidate_count"], 2)
            self.assertEqual(result["no_provider_candidate_count"], 1)
            self.assertEqual(
                len(result["ambiguous_exact_names"]["_ZprivateA"]["providers"]),
                2,
            )
            self.assertFalse(result["abi_compatibility_proven"])

    def test_overlapping_roots_do_not_duplicate_same_physical_provider(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            nested = root / "nested"
            nested.mkdir()
            archive = nested / "provider.a"
            archive.write_bytes(b"synthetic")

            def fake(cmd, **kwargs):
                path = cmd[-1]
                return SimpleNamespace(
                    returncode=0,
                    stdout=f"{path}[member.o]: _ZprivateUnique T 0 8\n",
                    stderr="",
                )

            with patch(
                "tools.etapa90.private_aot_sdk_provider_audit.subprocess.run",
                side_effect=fake,
            ):
                result = scan(
                    inventory(),
                    [("sdk-all", root), ("sdk-nested", nested)],
                    "fake-nm",
                )

            self.assertEqual(result["libraries_scanned"], 2)
            self.assertEqual(result["unique_provider_definitions_seen"], 1)
            self.assertEqual(result["exact_provider_candidate_count"], 1)
            self.assertEqual(result["ambiguous_provider_candidate_count"], 0)

    def test_rejects_nm_stderr_as_incomplete_scan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            archive = root / "provider.a"
            archive.write_bytes(b"synthetic")

            def fake(cmd, **kwargs):
                return SimpleNamespace(
                    returncode=0,
                    stdout=f"{cmd[-1]}[member.o]: _ZprivateUnique T 0 8\n",
                    stderr="warning: archive member skipped",
                )

            with patch(
                "tools.etapa90.private_aot_sdk_provider_audit.subprocess.run",
                side_effect=fake,
            ):
                result = scan(inventory(), [("sdk", root)], "fake-nm")

            self.assertFalse(result["all_provider_roots_scanned"])
            self.assertEqual(len(result["library_scan_errors"]), 1)
            self.assertEqual(result["exact_provider_candidate_count"], 0)

    def test_ignores_symlink_files_and_directories(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            real = root / "real"
            real.mkdir()
            (real / "inside.a").write_text("x")
            (root / "alias.a").symlink_to(real / "inside.a")
            (root / "alias-dir").symlink_to(real, target_is_directory=True)
            (root / "libversioned.so.1").write_text("x")
            found = provider_files(root)
            self.assertEqual(
                [path.relative_to(root).as_posix() for path in found],
                ["libversioned.so.1", "real/inside.a"],
            )

    def test_preserves_existing_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sdk = root / "sdk"
            sdk.mkdir()
            report = root / "out.json"
            report.write_text("old")
            destination = safe_report(report, [sdk], False)
            self.assertEqual(destination.name, "out_v2.json")
            self.assertEqual(report.read_text(), "old")

    def test_rejects_report_inside_provider_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaisesRegex(ValueError, "outside"):
                safe_report(root / "out.json", [root], False)

    def test_rejects_report_parent_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            real = root / "real"
            real.mkdir()
            alias = root / "alias"
            alias.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                safe_report(alias / "out.json", [], False)


if __name__ == "__main__":
    unittest.main()
