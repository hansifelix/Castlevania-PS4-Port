import unittest, tempfile
from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec
p=Path(__file__).resolve().parents[1]/'validar_build.py'
s=spec_from_file_location('kazuma26',p);m=module_from_spec(s);s.loader.exec_module(m)
def elf64_x64():
    a=bytearray(4096);a[:4]=b'\x7fELF';a[4]=2;a[5]=1;a[18:20]=(62).to_bytes(2,'little');return bytes(a)
class TestEtapa26(unittest.TestCase):
    def test_arquivo_ausente(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):m.analisar(Path(t))
    def test_elf_invalido(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t);(d/'triangle').write_bytes(b'X'*4096);(d/'eboot.bin').write_bytes(b'Y'*4096)
            with self.assertRaises(ValueError):m.analisar(d)
    def test_nao_confunde_link_com_runtime(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t);(d/'triangle').write_bytes(elf64_x64());(d/'eboot.bin').write_bytes(b'F'*4096)
            x=m.analisar(d)
            self.assertFalse(x['ps4_testado']);self.assertFalse(x['pkg_gerado'])
            self.assertFalse(x['runtime_castlevania_executado'])
            self.assertEqual(x['viabilidade_port'],'INDETERMINADA')
    def test_rejeita_eboot_duplicado(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t);(d/'triangle').write_bytes(elf64_x64());(d/'eboot.bin').write_bytes(b'F'*4096)
            (d/'sub').mkdir();(d/'sub'/'eboot.bin').write_bytes(b'A'*4096)
            with self.assertRaises(ValueError):m.analisar(d)
if __name__=='__main__':unittest.main()
