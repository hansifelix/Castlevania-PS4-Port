"""Etapa 86 — só objetos ELF criados de fontes artificiais neste teste."""
from pathlib import Path
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.etapa86.link_subsdk0_private import run_partial_link, inspect_archives, PIN


def fixture(base: Path, invalid_hash: bool = False) -> Path:
    (base / "first.c").write_text("extern int b(void); int a(void) { return b(); }\n")
    (base / "second.c").write_text("int b(void) { return 3; }\n")
    for i, source in enumerate(("first.c", "second.c")):
        subprocess.run(["cc", "-c", str(base / source), "-o", str(base / f"code_{i:03}.o")],
                       check=True, capture_output=True)
    archive = base / "test_objetos_privados.tar.gz"
    checksums = {f"code_{i:03}.o": hashlib.sha256((base / f"code_{i:03}.o").read_bytes()).hexdigest()
                 for i in range(2)}
    if invalid_hash:
        checksums["code_001.o"] = "0" * 64
    manifest = {"pin": PIN, "source_archive_sha256": "synthetic",
                "sha256": checksums}
    raw = json.dumps(manifest).encode()
    with tarfile.open(archive, "w:gz") as out:
        header = tarfile.TarInfo("manifest.json")
        header.size = len(raw)
        out.addfile(header, io.BytesIO(raw))
        for i in range(2):
            p = base / f"code_{i:03}.o"
            out.add(p, arcname=p.name)
    return archive


@unittest.skipUnless(shutil.which("cc") and shutil.which("ld.lld") and shutil.which("nm"),
                     "Teste de link precisa de cc, ld.lld e nm disponíveis")
class LinkTest(unittest.TestCase):
    def test_private_partial_link_with_2_synthetic_elf(self):
        with tempfile.TemporaryDirectory() as root:
            arch = fixture(Path(root))
            data = run_partial_link([arch], count=2, source_sha="synthetic")
            self.assertEqual(data["objetos_validados"], 2)
            self.assertTrue(data["partial_link_ok"])
            self.assertEqual(data["undefined_count"], 0)
            self.assertFalse(data["pkg_gerado"])

    def test_bad_checksum_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            arch = fixture(Path(root), invalid_hash=True)
            with tempfile.TemporaryDirectory() as staging:
                with self.assertRaisesRegex(ValueError, "SHA256"):
                    inspect_archives([arch], Path(staging), count=2, source_sha="synthetic")

    def test_missing_object_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            arch = fixture(Path(root))
            with tempfile.TemporaryDirectory() as staging:
                with self.assertRaisesRegex(ValueError, "Objetos ausentes"):
                    inspect_archives([arch], Path(staging), count=3, source_sha="synthetic")

    def test_duplicate_archive_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            arch = fixture(Path(root))
            with tempfile.TemporaryDirectory() as staging:
                with self.assertRaisesRegex(ValueError, "duplicado"):
                    inspect_archives([arch, arch], Path(staging), count=2, source_sha="synthetic")


if __name__ == "__main__":
    unittest.main()
