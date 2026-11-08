#!/usr/bin/env python3
"""PS4-only platform.h fix for pinned upstream nx/runtime sources.

Patches a temporary, pinned checkout in the CI or private AOT build,
not the upstream repository. Fails closed if the exact inline layout
has changed. No '__APPLE__' spoofing or source-wide regex substitutions.
"""
from pathlib import Path
import argparse

OLD = """#if defined(__APPLE__)
std::string writable_root();
#else
inline std::string writable_root() { return data_root(); }
#endif"""
NEW = """#if defined(__APPLE__) || defined(KAZUMA_PS4) || defined(KAZUMA_TEST_WRITABLE_ROOT)
std::string writable_root();
#else
inline std::string writable_root() { return data_root(); }
#endif"""


def patch(text: str) -> str:
    if text.count(OLD) != 1 or NEW in text:
        raise ValueError("Pinned nx/runtime platform.h ABI changed; no implicit overwrite")
    return text.replace(OLD, NEW, 1)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("platform_header", type=Path)
    args = p.parse_args()
    header = args.platform_header
    before = header.read_text(encoding="utf-8")
    after = patch(before)
    header.write_text(after, encoding="utf-8")
    print("PASS: PS4-specific writable_root declaration; app0 remains read-only")


if __name__ == "__main__":
    main()
