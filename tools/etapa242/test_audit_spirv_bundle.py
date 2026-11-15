"""Synthetic contract tests; neither game files nor real shader sources required."""
import csv
import json
from pathlib import Path
import struct
import tempfile
import unittest
from audit_spirv_bundle import AuditError, audit

A, B = "0123456789abcdef", "fedcba9876543210"
FIELDS = ["hash", "stage", "status", "spv_bytes"]


def spirv_module(model):
    # Header plus one OpEntryPoint (execution model, id, null-terminated "m").
    return struct.pack("<9I", 0x07230203, 0x00010500, 0, 2, 0,
                       (4 << 16) | 15, model, 1, 0x0000006D)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.inv = self.root / "inventory.json"
        self.all = self.root / "all-results.tsv"
        self.ok = self.root / "results.tsv"
        self.spv = self.root / "spv"
        self.spv.mkdir()
        self.validator = self.root / "spirv-val"
        self.validator.write_text("#!/bin/sh\n[ \"$1\" = '--target-env' ] && [ \"$2\" = 'vulkan1.2' ]\n")
        self.validator.chmod(0o700)
        self.records = [{"hash": A, "stage": "vertex", "required": True},
                        {"hash": B, "stage": "pixel", "required": False}]
        self.rows = [{"hash": A, "stage": "vertex", "status": "ok", "spv_bytes": "36"},
                     {"hash": B, "stage": "fragment", "status": "ok", "spv_bytes": "36"}]
        for h, model in ((A, 0), (B, 4)):
            (self.spv / (h + ".spv")).write_bytes(spirv_module(model))
        self.save()

    def save(self):
        self.inv.write_text(json.dumps({"programs": self.records}))
        for p, rows in ((self.all, self.rows), (self.ok, [r for r in self.rows if r["status"] in {"ok", "ok-retry"}])):
            with p.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=FIELDS, delimiter="\t")
                w.writeheader(); w.writerows(rows)

    def run_audit(self):
        return audit(self.inv, self.all, self.ok, self.spv, self.validator)

    def test_success(self):
        self.assertEqual(self.run_audit()["status"], "PASS")

    def test_missing_required_translation(self):
        self.rows[0]["status"] = "unsupported"
        self.save()
        self.assertEqual(self.run_audit()["failures"][0]["reason"], "REQUIRED_NOT_TRANSLATED")

    def test_optional_failure_is_allowed(self):
        self.rows[1]["status"] = "unsupported"
        self.save()
        self.assertEqual(self.run_audit()["status"], "PASS")

    def test_required_file_missing(self):
        (self.spv / (A + ".spv")).unlink()
        self.assertEqual(self.run_audit()["status"], "BLOCKED")

    def test_header_invalid(self):
        (self.spv / (B + ".spv")).write_bytes(b"BAD!" + bytes(16))
        self.rows[1]["spv_bytes"] = "20"
        self.save()
        self.assertEqual(self.run_audit()["status"], "BLOCKED")

    def test_exhaustiveness(self):
        self.rows.pop()
        self.save()
        with self.assertRaisesRegex(AuditError, "EXHAUSTIVE"):
            self.run_audit()

    def test_duplicate(self):
        self.records.append(self.records[0].copy())
        self.save()
        with self.assertRaisesRegex(AuditError, "DUPLICATE"):
            self.run_audit()

    def test_stage_mismatch(self):
        self.rows[1]["stage"] = "vertex"
        self.save()
        with self.assertRaisesRegex(AuditError, "STAGE_MISMATCH"):
            self.run_audit()

    def test_execution_model_mismatch(self):
        (self.spv / (A + ".spv")).write_bytes(spirv_module(4))
        self.assertEqual(self.run_audit()["failures"][0]["reason"],
                         "SPIRV_EXECUTION_MODEL_MISMATCH")

    def test_geometry_execution_model_is_blocked(self):
        (self.spv / (A + ".spv")).write_bytes(spirv_module(3))
        failure = self.run_audit()["failures"][0]
        self.assertEqual(failure["reason"],
                         "SPIRV_EXECUTION_MODEL_UNSUPPORTED_BY_RUNTIME")
        self.assertEqual(failure["execution_model"], 3)

    def test_entrypoint_missing(self):
        (self.spv / (A + ".spv")).write_bytes(
            struct.pack("<5I", 0x07230203, 0x00010500, 0, 2, 0)
        )
        self.rows[0]["spv_bytes"] = "20"
        self.save()
        self.assertEqual(self.run_audit()["failures"][0]["reason"],
                         "SPIRV_ENTRY_POINT_MISSING")

    def test_zero_instruction_word_count(self):
        (self.spv / (A + ".spv")).write_bytes(
            struct.pack("<6I", 0x07230203, 0x00010500, 0, 2, 0, 15)
        )
        self.rows[0]["spv_bytes"] = "24"
        self.save()
        self.assertEqual(self.run_audit()["failures"][0]["reason"],
                         "SPIRV_INSTRUCTION_WORD_COUNT_ZERO")

    def test_truncated_entrypoint_instruction(self):
        (self.spv / (A + ".spv")).write_bytes(
            struct.pack("<7I", 0x07230203, 0x00010500, 0, 2, 0,
                        (4 << 16) | 15, 0)
        )
        self.rows[0]["spv_bytes"] = "28"
        self.save()
        self.assertEqual(self.run_audit()["failures"][0]["reason"],
                         "SPIRV_INSTRUCTION_TRUNCATED")

    def test_fake_validator_failure(self):
        self.validator.write_text("#!/bin/sh\nexit 1\n")
        self.assertEqual(self.run_audit()["status"], "BLOCKED")

    def test_spv_symlink(self):
        actual = self.spv / (A + ".spv")
        target = self.root / "other"
        actual.rename(target); actual.symlink_to(target)
        self.assertEqual(self.run_audit()["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
