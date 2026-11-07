#!/usr/bin/env python3
"""Offline, read-only binary container preflight. Never executes a client.

Reports format/CPU and APK component evidence only. It does not validate
the publisher signature, analyze arbitrary code or indicate game compatibility.
No client files, credentials, package names, or game assets are uploaded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile

PE_MACHINES = {0x014C: "x86", 0x8664: "x86_64", 0xAA64: "arm64"}
ELF_MACHINES = {3: "x86", 62: "x86_64", 183: "arm64", 40: "arm32"}
APK_LIB_RE = re.compile(r"^lib/(arm64-v8a|armeabi-v7a|x86_64|x86)/([^/]+)\.so$", re.I)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect(path: Path, compute_hash: bool = False) -> dict:
    """Read-only format identification; no execution/unpacking of inputs."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("Input must be an existing regular file, not a symlink")
    size = path.stat().st_size
    with path.open("rb") as stream:
        header = stream.read(64)
    out = {
        "format": "unknown",
        "architecture": "unknown",
        "bytes": size,
        "sha256": _sha256(path) if compute_hash else None,
        "executes_game": False,
        "ps4_compatible": "not_tested",
        "signature_verified": False,
    }

    if zipfile.is_zipfile(path):
        try:
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                has_manifest = "AndroidManifest.xml" in names
                has_dex = any(re.fullmatch(r"classes(\d*)\.dex", x) for x in names)
                architectures: set[str] = set()
                lib_names: set[str] = set()
                for name in names:
                    found = APK_LIB_RE.fullmatch(name)
                    if found:
                        architectures.add(found.group(1).lower())
                        lib_names.add(found.group(2).lower())
                out["format"] = "android_apk" if has_manifest else "zip_other"
                out["architecture"] = ",".join(sorted(architectures)) or "unknown"
                out["android_evidence"] = {
                    "has_android_manifest": has_manifest,
                    "has_dex": has_dex,
                    "native_architectures": sorted(architectures),
                    "has_unity_native_library": "libunity" in lib_names,
                    "has_il2cpp_native_library": "libil2cpp" in lib_names,
                    "entry_count": len(names),
                }
                out["assessment"] = (
                    "APK Android is NOT a native PS4 executable; platform adaptation required."
                    if has_manifest else "ZIP: not an Android client proven by format alone."
                )
                return out
        except (zipfile.BadZipFile, RuntimeError, OSError, ValueError) as exc:
            raise ValueError("Invalid or unreadable ZIP structure") from exc

    if len(header) >= 64 and header[:2] == b"MZ":
        offset = struct.unpack_from("<I", header, 0x3C)[0]
        if offset <= size - 6 and offset <= 1024 * 1024:
            with path.open("rb") as stream:
                stream.seek(offset)
                pe = stream.read(6)
            if len(pe) == 6 and pe[:4] == b"PE\0\0":
                machine = struct.unpack_from("<H", pe, 4)[0]
                out.update({
                    "format": "windows_pe",
                    "architecture": PE_MACHINES.get(machine, f"unknown_0x{machine:04x}"),
                    "assessment": (
                        "Windows PE is NOT a native PS4 executable even when CPU is x86_64; "
                        "Windows and graphics interfaces require adaptation."
                    ),
                })
                return out

    if len(header) >= 20 and header[:4] == b"\x7fELF":
        endianness = {1: "<", 2: ">"}.get(header[5])
        bits = {1: "32", 2: "64"}.get(header[4], "unknown")
        if endianness:
            machine = struct.unpack_from(endianness + "H", header, 18)[0]
            out.update({
                "format": "elf",
                "architecture": ELF_MACHINES.get(machine, f"unknown_{machine}") + "/" + bits,
                "assessment": "ELF architecture alone does NOT establish PS4 ABI compatibility.",
            })
            return out

    out["assessment"] = "No recognized native executable or APK format."
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only local client format audit")
    parser.add_argument("file", type=Path, help="Local file path (do not upload it)")
    parser.add_argument("--sha256", action="store_true", help="Hash all bytes, can be slow")
    args = parser.parse_args()
    try:
        result = inspect(args.file, compute_hash=args.sha256)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
