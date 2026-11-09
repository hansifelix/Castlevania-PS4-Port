#!/usr/bin/env python3
"""Fail-closed audit of every SPIR-V referenced by an upstream translation batch.

Host-side only. No proprietary code, shaders, or keys are stored in this tool.
Requires real spirv-val in production, invoked for EACH successful module.
"""
import argparse
import csv
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

SHA16 = re.compile(r"[0-9a-f]{16}\Z")
OK = {"ok", "ok-retry"}
MAGIC = 0x07230203


class AuditError(Exception):
    pass


def inventory(path):
    source = json.loads(path.read_text(encoding="utf-8"))
    items = source["programs"]
    if not isinstance(items, list) or not items:
        raise AuditError("EMPTY_INVENTORY")
    records = {}
    for item in items:
        key = item["hash"]
        if not isinstance(key, str) or not SHA16.fullmatch(key) or key in records:
            raise AuditError("DUPLICATE_OR_INVALID_INVENTORY_HASH")
        if type(item.get("required")) is not bool or not isinstance(item.get("stage"), str):
            raise AuditError("INVALID_INVENTORY_RECORD")
        records[key] = item
    return records


def read_results(path):
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter="\t")
        if not reader.fieldnames or not {"hash", "stage", "status", "spv_bytes"}.issubset(reader.fieldnames):
            raise AuditError("MISSING_TSV_FIELDS")
        result = {}
        for row in reader:
            key = row["hash"]
            if not isinstance(key, str) or not SHA16.fullmatch(key) or key in result:
                raise AuditError("DUPLICATE_OR_INVALID_TSV_HASH")
            result[key] = row
    return result


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def audit(inv, all_tsv, success_tsv, spv_root, validator):
    records = inventory(inv)
    all_rows, successful_rows = read_results(all_tsv), read_results(success_tsv)
    if set(all_rows) != set(records):
        raise AuditError("ALL_RESULTS_NOT_EXHAUSTIVE")
    expected_successes = {h for h, row in all_rows.items() if row["status"] in OK}
    if set(successful_rows) != expected_successes:
        raise AuditError("SUCCESS_RESULTS_INCONSISTENT")
    if not validator.is_file() or not os.access(validator, os.X_OK):
        raise AuditError("SPIRV_VAL_NOT_EXECUTABLE")
    failures = []
    for h in sorted(records):
        item = records[h]
        row = all_rows[h]
        expected_stage = "fragment" if item["stage"] == "pixel" else item["stage"]
        if row["stage"] != expected_stage:
            raise AuditError("STAGE_MISMATCH")
        if h not in expected_successes:
            if item["required"]:
                failures.append({"hash": h, "reason": "REQUIRED_NOT_TRANSLATED"})
            continue
        if successful_rows[h] != row:
            raise AuditError("SUCCESS_METADATA_DIFFERS")
        file = spv_root / (h + ".spv")
        if file.is_symlink() or not file.is_file():
            failures.append({"hash": h, "reason": "MISSING_OR_SYMLINK_SPV"})
            continue
        n = file.stat().st_size
        try:
            expected_bytes = int(row["spv_bytes"])
        except (TypeError, ValueError):
            raise AuditError("INVALID_SPV_BYTES")
        if n < 20 or n % 4 or n != expected_bytes:
            failures.append({"hash": h, "reason": "SPV_SIZE_INVALID"})
            continue
        with file.open("rb") as stream:
            magic, version, _generator, bound, reserved = struct.unpack("<5I", stream.read(20))
        if magic != MAGIC or (version >> 16) != 1 or ((version >> 8) & 0xff) > 6 or (version & 0xff) != 0 or bound == 0 or reserved:
            failures.append({"hash": h, "reason": "SPV_HEADER_INVALID"})
            continue
        try:
            proc = subprocess.run([str(validator), "--target-env", "vulkan1.2", str(file)],
                                  capture_output=True, timeout=30, check=False)
            if proc.returncode:
                failures.append({"hash": h, "reason": "SPIRV_VAL_FAILED"})
        except subprocess.TimeoutExpired:
            failures.append({"hash": h, "reason": "SPIRV_VAL_TIMEOUT"})
    return {"etapa": 242,
            "status": "PASS" if not failures else "BLOCKED",
            "inventory_count": len(records),
            "required_count": sum(1 for r in records.values() if r["required"]),
            "successful_results": len(expected_successes),
            "failures": failures,
            "validated_target": "vulkan1.2",
            "ps4_boot": "NOT_TESTED"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for k in ("inventory", "all-results", "results", "spirv-dir", "spirv-val", "report"):
        p.add_argument("--" + k, type=Path, required=True)
    a = vars(p.parse_args())
    report = a.pop("report")
    try:
        summary = audit(a["inventory"], a["all_results"], a["results"], a["spirv_dir"], a["spirv_val"])
    except (OSError, ValueError, KeyError, TypeError, AuditError, json.JSONDecodeError) as exc:
        summary = {"etapa": 242, "status": "BLOCKED", "reason": str(exc)[:90], "ps4_boot": "NOT_TESTED"}
    atomic_json(report, summary)
    print("KAZUMA242_" + summary["status"])
    return 0 if summary["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
