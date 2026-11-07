"""Preflight SDK: fixtures produzidas aqui, sem arquivos comerciais."""
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.sdk_compile.sdk_cpp_preflight import inspect_archive


def make(archive, sources):
    with tarfile.open(archive, "w:gz") as t:
        for name, text in sources.items():
            contents = text.encode("utf-8")
            info = tarfile.TarInfo("synthetic/" + name)
            info.size = len(contents)
            t.addfile(info, io.BytesIO(contents))


class SDKPreflightTests(unittest.TestCase):
    def test_counts_and_stg(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "synthetic.tar.gz"
            make(p, {"code_000.cpp": 'std::countl_zero(0u); std::countl_zero(1u);\n'
                                          'nx::unimpl(c, 0x20, "stg x8, [x8]");\n',
                     "code_001.cpp": 'nx::unimpl(c, 0x24, "udf");\n'})
            v = inspect_archive(p, expected=2)
            self.assertEqual(v["countl_zero_files"], 1)
            self.assertEqual(v["countl_zero_calls"], 2)
            self.assertEqual(v["stg_units"], ["code_000.cpp"])
            self.assertEqual(v["static_unimpl_categories"], {"stg": 1, "udf": 1})
            self.assertFalse(v["ps4_compiled"])

    def test_incomplete_archive_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "synthetic.tar.gz"
            make(p, {"code_000.cpp": "void f(){}"})
            with self.assertRaisesRegex(ValueError, "todos"):
                inspect_archive(p, expected=2)

    def test_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "synthetic.tar.gz"
            with tarfile.open(p, "w:gz") as t:
                for _ in range(2):
                    raw = b"void f(){}"
                    info = tarfile.TarInfo("x/code_000.cpp")
                    info.size = len(raw)
                    t.addfile(info, io.BytesIO(raw))
            with self.assertRaisesRegex(ValueError, "duplicado"):
                inspect_archive(p, expected=1)

    def test_wrong_sha_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "synthetic.tar.gz"
            make(p, {"code_000.cpp": "void f(){}"})
            with self.assertRaisesRegex(ValueError, "SHA256"):
                inspect_archive(p, expected=1, sha256="f" * 64)

    def test_no_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "synthetic.tar.gz"
            with tarfile.open(p, "w:gz") as t:
                info = tarfile.TarInfo("x/code_000.cpp")
                info.type = tarfile.SYMTYPE
                info.linkname = "../../secrets"
                t.addfile(info)
            with self.assertRaisesRegex(ValueError, "regular"):
                inspect_archive(p, expected=1)


if __name__ == "__main__":
    unittest.main()
