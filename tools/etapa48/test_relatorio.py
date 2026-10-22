import unittest
import tempfile
from pathlib import Path
from relatorio import analyze, extract_symbols, classification

class RealBootTests(unittest.TestCase):
    def test_parse(self):
        src='U nx::plat::audio_open(void (*)(void*))\nld.lld: error: undefined symbol: nx::linked_modules()\n >>> referenced by foo\n'
        self.assertEqual(len(extract_symbols(src)),2)
    def test_groups(self):
        self.assertEqual(classification('nx::game::first_frame()'),'MODULOS_DO_JOGO_AUSENTES')
        self.assertEqual(classification('nx::plat::read_pad(x)'),'PLATAFORMA_PS4_PENDENTE')
        self.assertEqual(classification('__cxa_throw'),'CXX_ABI')
    def test_report(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)
            (p/'SIMBOLOS_PENDENTES_BOOT.txt').write_text('U nx::linked_modules()\nU nx::plat::audio_open()\nU __cxa_throw\n')
            (p/'LINK_ESTRITO_BOOT.log').write_text('ld.lld: error: undefined symbol: nx::game::first_frame()\n')
            r=analyze(p, 'PASSOU','PASSOU','FALHOU')
            self.assertEqual(r['simbolos_pendentes_objeto'],3)
            self.assertEqual(r['grupos']['MODULOS_DO_JOGO_AUSENTES'],1)
            self.assertTrue((p/'LEIA_PRIMEIRO.txt').exists())
if __name__=='__main__':unittest.main()
