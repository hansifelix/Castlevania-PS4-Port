import tempfile,unittest
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
src=Path(__file__).resolve().parents[1]/'verificar_pacote.py'
spec=spec_from_file_location('kazuma27',src);mod=module_from_spec(spec);spec.loader.exec_module(mod)

def elf64():
    d=bytearray(4096);d[:4]=b'\x7fELF';d[4]=2;d[5]=1;d[18:20]=(62).to_bytes(2,'little');return d

def fixture(p):
    (p/'triangle').write_bytes(elf64());(p/'eboot.bin').write_bytes(b'F'*4096)

class Teste(unittest.TestCase):
    def test_rejeita_ausente(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):mod.verificar(Path(td))
    def test_rejeita_elf_invalido(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);fixture(d);(d/'triangle').write_bytes(b'x'*4096)
            with self.assertRaises(ValueError):mod.verificar(d)
    def test_rejeita_pkg_com_nome_incorreto(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);fixture(d);(d/'errado.pkg').write_bytes(b'A'*262145)
            with self.assertRaises(ValueError):mod.verificar(d,d)
    def test_rejeita_duplicado_eboot(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);fixture(d);(d/'sub').mkdir();(d/'sub/eboot.bin').write_bytes(b'A'*4096)
            with self.assertRaises(ValueError):mod.verificar(d)
    def test_relatorio_nao_afirma_gpu_testada(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);fixture(d);r=mod.verificar(d)
            self.assertFalse(r['gpu_ps4_testada']);self.assertFalse(r['castlevania_executado'])
            self.assertEqual(r['title_id'],'BREW91240')
if __name__=='__main__':unittest.main()
