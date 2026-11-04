"""Testes com bytes sintéticos; nenhum conteúdo comercial."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.etapa76.exefs_preflight import inspect_module, inspect_exefs, MODULES


def fake_nso(path: Path, build_id: bytes = b'\x11' * 32):
    blob = bytearray(0x104)
    blob[0:4] = b'NSO0'
    struct.pack_into('<III', blob, 0x10, 0x100, 0, 4)
    struct.pack_into('<I', blob, 0x60, 4)
    blob[0x40:0x60] = build_id
    blob[0x100:0x104] = b'TEST'
    path.write_bytes(blob)


class PreflightTest(unittest.TestCase):
    def test_missing_modules_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            fake_nso(Path(d) / 'main')
            result = inspect_exefs(Path(d))
            self.assertFalse(result['entradas_exefs_validas'])
            self.assertFalse(result['modulos']['sdk']['ok'])

    def test_complete_synthetic_exefs(self):
        with tempfile.TemporaryDirectory() as d:
            for name in MODULES:
                fake_nso(Path(d) / name)
            result = inspect_exefs(Path(d))
            self.assertTrue(result['entradas_exefs_validas'])
            self.assertFalse(result['versao_1_1_0_verificada'])
            self.assertEqual(result['modulos']['main']['segmentos'][0]['bytes_armazenados'], 4)

    def test_truncated_segment_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'main'
            fake_nso(path)
            raw = bytearray(path.read_bytes())
            struct.pack_into('<I', raw, 0x18, 10000)
            path.write_bytes(raw)
            self.assertFalse(inspect_module(path)['ok'])

    def test_bad_magic_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'main'
            path.write_bytes(b'X' * 512)
            self.assertFalse(inspect_module(path)['ok'])

    def test_version_reference_does_not_infer_game_version(self):
        with tempfile.TemporaryDirectory() as d:
            for name in MODULES:
                fake_nso(Path(d) / name)
            exp = {name: '11' * 32 for name in MODULES}
            report = inspect_exefs(Path(d), exp)
            self.assertTrue(report['entradas_exefs_validas'])
            self.assertTrue(report['build_ids_conferidos'])
            self.assertFalse(report['versao_1_1_0_verificada'])
            exp['sdk'] = 'ff' * 32
            self.assertFalse(inspect_exefs(Path(d), exp)['entradas_exefs_validas'])

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            fake_nso(path / 'main')
            (path / 'sdk').symlink_to(path / 'main')
            self.assertFalse(inspect_module(path / 'sdk')['ok'])


if __name__ == '__main__':
    unittest.main()
