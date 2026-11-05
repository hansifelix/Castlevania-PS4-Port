"""Etapa 77: testes apenas com módulos NSO sintéticos, nunca comerciais."""
from pathlib import Path
import hashlib
import json
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.etapa77.verify_revision import verify_exefs, load_profile, REFERENCE, sha256_file

MODULES = ("main", "sdk", "subsdk0")


def synth_nso(path: Path, ident: int) -> bytes:
    buf = bytearray(0x104)
    buf[:4] = b"NSO0"
    struct.pack_into("<III", buf, 0x10, 0x100, 0, 4)
    struct.pack_into("<I", buf, 0x60, 4)
    buf[0x40:0x60] = bytes((ident,)) * 32
    buf[0x100:] = b"TEST"
    raw = bytes(buf)
    path.write_bytes(raw)
    return raw


def fixture(root: Path):
    entries = []
    for ident, name in enumerate(MODULES, 1):
        data = synth_nso(root / name, ident)
        entries.append({
            "name": name,
            "build_id": (bytes((ident,)) * 32).hex(),
            "nso_sha256_reference": hashlib.sha256(data).hexdigest(),
        })
    return {"content_version": "1.1.0", "modules": entries, "source_commit": "TEST_SYNTHETIC"}


class ExactRevisionTest(unittest.TestCase):
    def test_triple_match(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            profile = fixture(root)
            r = verify_exefs(root, profile)
            self.assertTrue(r["correspondencia_exata_ao_perfil"])
            self.assertEqual(len(r["modulos"]), 3)
            self.assertFalse(r["recompilacao_aot_feita"])
            self.assertFalse(r["romfs_validada"])

    def test_modified_data_fails_sha_even_if_build_id_matches(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            profile = fixture(root)
            with (root / "main").open("ab") as stream:
                stream.write(b"ALTERADO")
            r = verify_exefs(root, profile)
            self.assertFalse(r["correspondencia_exata_ao_perfil"])
            self.assertTrue(r["modulos"]["main"]["build_id_confere"])
            self.assertFalse(r["modulos"]["main"]["sha256_nso_confere"])

    def test_wrong_build_id_fails_even_if_hash_in_profile_matches(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            profile = fixture(root)
            profile["modules"][0]["build_id"] = "ff" * 32
            r = verify_exefs(root, profile)
            self.assertFalse(r["correspondencia_exata_ao_perfil"])
            self.assertTrue(r["modulos"]["main"]["sha256_nso_confere"])
            self.assertFalse(r["modulos"]["main"]["build_id_confere"])

    def test_missing_module(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            profile = fixture(root)
            (root / "sdk").unlink()
            self.assertFalse(verify_exefs(root, profile)["correspondencia_exata_ao_perfil"])

    def test_truncated_nso(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            profile = fixture(root)
            (root / "subsdk0").write_bytes(b"NSO0")
            r = verify_exefs(root, profile)
            self.assertFalse(r["modulos"]["subsdk0"]["identidade_confirmada"])

    def test_symlink_refused(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            profile = fixture(root)
            (root / "sdk").unlink()
            (root / "sdk").symlink_to(root / "main")
            self.assertFalse(verify_exefs(root, profile)["modulos"]["sdk"]["identidade_confirmada"])

    def test_reference_file_structure(self):
        p = load_profile(REFERENCE)
        self.assertEqual(p["content_version"], "1.1.0")
        self.assertEqual({m["name"] for m in p["modules"]}, set(MODULES))
        self.assertEqual(p["source_commit"], "4043f21bb4f656d34cd17ba070238c7728d00631")

    def test_streaming_digest(self):
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "small"
            data = b"a" * (1024 * 1024 + 11)
            path.write_bytes(data)
            self.assertEqual(sha256_file(path), hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    unittest.main()
