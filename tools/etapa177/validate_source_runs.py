#!/usr/bin/env python3
"""Fail-closed provenance checks for selected AOT object-producing GitHub runs.

Do not read or publish any game content. Called before downloading seven large
private object archives, after selecting candidate run ids from the artifact API.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

REQUIRED = {
    "main": ".github/workflows/lingshu-etapa153-main-objetos-privados.yml",
    "sdk": ".github/workflows/lingshu-etapa152-sdk-subdk-objetos.yml",
}
SHA40 = re.compile(r"[0-9a-f]{40}\Z")


def require_run(run: dict, kind: str, repository: str, branch: str) -> str:
    if not isinstance(run, dict):
        raise ValueError(f"{kind}: invalid GitHub run payload")
    if run.get("path") != REQUIRED[kind]:
        raise ValueError(f"{kind}: wrong workflow path")
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise ValueError(f"{kind}: source run is not completed/success")
    if run.get("head_branch") != branch:
        raise ValueError(f"{kind}: source branch mismatch")
    if run.get("event") not in ("workflow_dispatch", "push"):
        raise ValueError(f"{kind}: unexpected workflow trigger")
    if not isinstance(run.get("id"), int) or run["id"] <= 0:
        raise ValueError(f"{kind}: invalid workflow run id")
    for key in ("repository", "head_repository"):
        parent = run.get(key)
        if not isinstance(parent, dict) or parent.get("full_name") != repository:
            raise ValueError(f"{kind}: {key} is not expected private repository")
    head = run.get("head_sha")
    if not isinstance(head, str) or not SHA40.fullmatch(head):
        raise ValueError(f"{kind}: invalid source commit SHA")
    return head


def validate(main: dict, sdk: dict, repository: str, branch: str,
             main_id: int, sdk_id: int) -> str:
    if main.get("id") != main_id or sdk.get("id") != sdk_id:
        raise ValueError("GitHub run payload does not match selected AOT artifact run ids")
    main_head = require_run(main, "main", repository, branch)
    sdk_head = require_run(sdk, "sdk", repository, branch)
    if main_head != sdk_head:
        raise ValueError("MAIN and SDK/SUBSDK0 compiled from different Git commits")
    return main_head


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-json", required=True, type=Path)
    parser.add_argument("--sdk-json", required=True, type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--main-run", required=True, type=int)
    parser.add_argument("--sdk-run", required=True, type=int)
    args = parser.parse_args()
    try:
        main_run = json.loads(args.main_json.read_text("utf-8"))
        sdk_run = json.loads(args.sdk_json.read_text("utf-8"))
        source_head = validate(
            main_run, sdk_run, args.repository, args.branch,
            args.main_run, args.sdk_run)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"LINGSHU177_PRIVATE_SOURCE_PROVENANCE=REJECTED: {exc}",
              file=sys.stderr)
        return 2
    print(f"LINGSHU177_PRIVATE_SOURCE_PROVENANCE=PASS_SAME_BRANCH_SUCCESSFUL_RUNS_SAME_SHA")
    print(f"LINGSHU177_SOURCE_SHA={source_head}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
