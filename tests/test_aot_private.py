"""Etapa 79 — testes sem arquivos do jogo (somente fixture e diretórios temporários)."""
from pathlib import Path
import hashlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.etapa79.make_synthetic_nso import make_fixture, FUNCTION_START
from tools.etapa79.aot_private import (digest, validate_input, check_output,
                                       build_command, PINNED)


class Stage79Test(unittest.TestCase):
    def test_fixture_is_nso_with_header_mod0_pointer(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "fixture.nso"
            make_fixture(p)
            data = p.read_bytes()
            self.assertEqual(data[:4], b"NSO0")
            self.assertEqual(len(data), 0x340)
            # text segment raw offset = 0x100; arm64 entry in image = 0x20.
            self.assertEqual(int.from_bytes(data[0x14:0x18], "little"), FUNCTION_START)
            self.assertEqual(int.from_bytes(data[0x124:0x128], "little"), 0x220)
            self.assertEqual(digest(p), hashlib.sha256(data).hexdigest())

    def test_private_input_must_match_sha_and_build_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "subsdk0"
            make_fixture(path)
            data = path.read_bytes()
            profile = {"modules": [{
                "name": "subsdk0",
                "build_id": data[0x40:0x60].hex(),
                "nso_sha256_reference": hashlib.sha256(data).hexdigest(),
            }]}
            self.assertEqual(validate_input(root, "subsdk0", profile)["name"], "subsdk0")
            profile["modules"][0]["nso_sha256_reference"] = "ff" * 32
            with self.assertRaisesRegex(ValueError, "SHA256"):
                validate_input(root, "subsdk0", profile)

    def test_output_refuses_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "repo" / ".git").mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "Git"):
                check_output(root / "repo" / "private", root / "exe", root / "upstream")

    def test_output_refuses_exefs_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "ExeFS"):
                check_output(root / "exe" / "output", root / "exe", root / "upstream")

    def test_output_refuses_existing_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "generated"
            output.mkdir()
            (output / "keep.txt").write_text("preserve")
            with self.assertRaisesRegex(ValueError, "vazio"):
                check_output(output, root / "exe", root / "upstream")

    def test_cli_command_uses_pinned_entrypoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cmd = build_command("python3", root / "exe", root / "generated",
                                root / "upstream", "subsdk0", "0x4020000000", None)
            self.assertEqual(cmd[1:3], ["-m", "recomp"])
            self.assertIn("--exceptions", cmd)
            self.assertNotIn("--patches", cmd)
            self.assertNotIn("--only", cmd)

    def test_main_requires_resolution_patches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "Patches"):
                build_command("python3", root / "exe", root / "generated",
                              root / "upstream", "main", "0x4000000000", None)

    def test_invalid_only_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "hexadecimal"):
                build_command("python3", root / "exe", root / "generated",
                              root / "upstream", "sdk", "0x4010000000", "20")

    def test_checkout_commit_is_explicit(self):
        self.assertEqual(PINNED, "4043f21bb4f656d34cd17ba070238c7728d00631")


if __name__ == "__main__":
    unittest.main()
