import json
import pathlib
import struct
import unittest
import ast
ROOT=pathlib.Path(__file__).resolve().parents[3]
class Gate(unittest.TestCase):
    def test_instrucoes_reais_aarch64(self):
        code=(0x52800540,0x11000400,0xD65F03C0)
        self.assertEqual(struct.pack('<3I',*code).hex(),'4005805200040011c0035fd6')
    def test_fonte_usando_emissor_real(self):
        s=(ROOT/'tools/etapa21/gerar_recomp_sintetico.py').read_text()
        self.assertIn('analysis.analyze(m',s)
        self.assertIn('emit.Emitter(an',s)
        self.assertIn('e.function(an.functions[0])',s)
        self.assertIn('e.handled != 3',s)
    def test_sem_publicacao_de_dados_de_jogo(self):
        flow=(ROOT/'.github/workflows/kazuma-etapa21-recomp-arm64.yml').read_text()
        build=(ROOT/'tools/etapa21/compilar_recomp_ps4.sh').read_text()
        self.assertNotIn('pkg_build',flow+build)
        self.assertNotIn('create-fself',flow+build)
        self.assertIn('010ed7a596a621c15d3a8dfa5795ca8c3668b066',flow)
        self.assertIn('4043f21bb4f656d34cd17ba070238c7728d00631',flow)
    def test_python_sintaxe(self):
        p=ROOT/'tools/etapa21/gerar_recomp_sintetico.py'
        ast.parse(p.read_text())
if __name__=='__main__':unittest.main()
