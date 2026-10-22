import importlib.util,unittest, tempfile, subprocess
from pathlib import Path
from unittest.mock import patch,Mock
spec=importlib.util.spec_from_file_location('v',Path(__file__).resolve().parents[1]/'validar_arquivo.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class Tests(unittest.TestCase):
    def test_arquivo_ausente(self):
        with self.assertRaises(ValueError):v.inspect_archive(Path('/tmp/arquivo_que_nao_existe_01.a'))
    def test_arquivo_muito_pequeno(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'x.a';a.write_bytes(b'12345')
            with self.assertRaises(ValueError):v.inspect_archive(a)
    def test_arquivo_com_conteudo_insuficiente(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'x.a';a.write_bytes(b'X'*4097)
            def fake(cmd,**kw):
                if cmd[1]=='t':return Mock(stdout='a.o\nb.o\n')
                return Mock(stdout='T symbol\n')
            with patch.object(v.subprocess,'run',side_effect=fake):
                with self.assertRaises(ValueError):v.inspect_archive(a)
    def test_contagem_sem_prometer_port(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'x.a';a.write_bytes(b'X'*4097)
            def fake(cmd,**kw):
                if cmd[1]=='t':return Mock(stdout='\n'.join('x'+str(i)+'.o' for i in range(12)))
                return Mock(stdout='\n'.join('a T sym'+str(i) for i in range(18)))
            with patch.object(v.subprocess,'run',side_effect=fake):
                r=v.inspect_archive(a)
            self.assertEqual(r['objetos'],12)
            self.assertFalse(r['mesa_radv_compilada'])
            self.assertFalse(r['ps4_testado'])
            self.assertEqual(r['port_viavel'],'INDETERMINADO')
if __name__=='__main__':unittest.main()
