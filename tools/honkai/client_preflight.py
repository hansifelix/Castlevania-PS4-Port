#!/usr/bin/env python3
"""Offline, read-only binary container preflight. Never executes a client.

Reports format/CPU and APK component evidence only. It does not validate
the publisher signature, analyze arbitrary code or indicate game compatibility.
No client files, credentials, package names, or game assets are uploaded.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re
import stat
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




# Conservative metadata thresholds, not a virus/malware detector.
MAX_ZIP_ENTRIES = 100_000
MAX_ZIP_UNCOMPRESSED = 16 * 1024**3
MAX_COMPRESSION_RATIO = 2_000

def _check_zip_metadata(infos: list[zipfile.ZipInfo]) -> None:
    """Reject ambiguous/abusive ZIP metadata before reading any member contents."""
    if len(infos) > MAX_ZIP_ENTRIES:
        raise ValueError("ZIP has too many entries")
    names: set[str] = set()
    total = 0
    for info in infos:
        name = info.filename
        if not name or name in names:
            raise ValueError("ZIP contains an empty/duplicate name")
        names.add(name)
        if (
            name.startswith("/")
            or "\\" in name
            or any(p in {".", ".."} for p in name.split("/"))
        ):
            raise ValueError("ZIP contains an unsafe path")
        if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
            raise ValueError("ZIP contains symlink")
        if info.flag_bits & 0x1:
            raise ValueError("Encrypted ZIP entries unsupported")
        total += info.file_size
        if total > MAX_ZIP_UNCOMPRESSED:
            raise ValueError("ZIP uncompressed size is excessive")
        if info.file_size and (
            info.compress_size == 0
            or info.file_size > info.compress_size * MAX_COMPRESSION_RATIO
        ):
            raise ValueError("ZIP contains suspicious compression ratio")


def _native_elf_arch(header: bytes) -> str | None:
    """Determine library ELF ABI from its actual header, not APK path labels."""
    if len(header) < 20 or header[:4] != b"\x7fELF":
        return None
    cls, endian = header[4], header[5]
    if cls not in (1, 2) or endian not in (1, 2):
        return None
    machine = struct.unpack_from(("<" if endian == 1 else ">") + "H", header, 18)[0]
    return {
        (1, 3): "x86",
        (2, 62): "x86_64",
        (1, 40): "armeabi-v7a",
        (2, 183): "arm64-v8a",
    }.get((cls, machine))


def inspect(path: Path, compute_hash: bool = False, expected_sha256: str | None = None) -> dict:
    """Read-only format identification; no execution/unpacking of inputs."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("Input must be an existing regular file, not a symlink")
    size = path.stat().st_size
    with path.open("rb") as stream:
        header = stream.read(64)
    if expected_sha256 is not None:
        if not re.fullmatch(r"[a-fA-F0-9]{64}", expected_sha256):
            raise ValueError("Expected SHA-256 must be exactly 64 hexadecimal characters")
        calculated = _sha256(path)
        if not hmac.compare_digest(calculated, expected_sha256.lower()):
            raise ValueError("SHA-256 mismatch: input differs from the trusted reference")
    else:
        calculated = _sha256(path) if compute_hash else None
    out = {
        "format": "unknown",
        "architecture": "unknown",
        "bytes": size,
        "sha256": calculated,
        "reference_hash_matches": expected_sha256 is not None,
        "malware_free": "not_evaluated",
        "executes_game": False,
        "ps4_compatible": "not_tested",
        "signature_verified": False,
    }

    if zipfile.is_zipfile(path):
        try:
            with zipfile.ZipFile(path) as archive:
                entries = archive.infolist()
                _check_zip_metadata(entries)
                names = [entry.filename for entry in entries]
                has_manifest = "AndroidManifest.xml" in names
                has_dex = any(re.fullmatch(r"classes(\d*)\.dex", x) for x in names)
                architectures: set[str] = set()
                lib_names: set[str] = set()
                native_header_checked = 0
                native_header_matching = 0
                native_header_mismatch = 0
                native_header_invalid = 0
                for info in archive.infolist():
                    found = APK_LIB_RE.fullmatch(info.filename)
                    if not found:
                        continue
                    declared_arch = found.group(1).lower()
                    architectures.add(declared_arch)
                    lib_names.add(found.group(2).lower())
                    # Only 32 bytes are needed for ELF class/arch; no extraction.
                    with archive.open(info, "r") as stream:
                        elf_header = stream.read(32)
                    native_header_checked += 1
                    actual_arch = _native_elf_arch(elf_header)
                    if actual_arch is None:
                        native_header_invalid += 1
                    elif actual_arch != declared_arch:
                        native_header_mismatch += 1
                    else:
                        native_header_matching += 1
                out["format"] = "android_apk" if has_manifest else "zip_other"
                out["architecture"] = ",".join(sorted(architectures)) or "unknown"
                out["android_evidence"] = {
                    "has_android_manifest": has_manifest,
                    "has_dex": has_dex,
                    "native_architectures": sorted(architectures),
                    "has_unity_native_library": "libunity" in lib_names,
                    "has_il2cpp_native_library": "libil2cpp" in lib_names,
                    "entry_count": len(names),
                    "duplicate_zip_entries": len(names) - len(set(names)),
                    "native_header_checked": native_header_checked,
                    "native_header_matching": native_header_matching,
                    "native_header_mismatch": native_header_mismatch,
                    "native_header_invalid": native_header_invalid,
                    "native_library_abi_consistent": (
                        native_header_checked > 0
                        and native_header_mismatch == 0
                        and native_header_invalid == 0
                    ),
                }
                out["assessment"] = (
                    "APK Android is NOT a native PS4 executable; platform adaptation required."
                    if has_manifest else "ZIP: not an Android client proven by format alone."
                )
                return out
        except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
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
    parser.add_argument("--expected-sha256", help="Compare with an independently trusted SHA-256 reference")
    args = parser.parse_args()
    try:
        result = inspect(args.file, compute_hash=args.sha256, expected_sha256=args.expected_sha256)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
