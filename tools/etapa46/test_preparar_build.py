import unittest
from pathlib import Path
from preparar_build import derive

class SmokeBuild(unittest.TestCase):
    def test_essential_markers(self):
        # Testa marcadores independentemente do builder real (ele sera validado no runner).
        code=Path('tools/etapa46/preparar_build.py').read_text()
        for name in ('BREW94608','KAZUMA46PERF0000','platform_ps4_files.cpp','platform_ps4_core.cpp','kazuma46.dat'):
            self.assertIn(name,code)
    def test_benchmark_contract(self):
        data=Path('tools/etapa46/tela_kazuma.cpp').read_text()
        self.assertIn('KAZUMA46: DIAG_START',data)
        self.assertIn('make_dirs("")',data)
        self.assertIn('PERF FPS_X10=',data)
        self.assertIn('clock_ok=false',data)
        self.assertIn('ORBIS_PAD_BUTTON_TRIANGLE',data)
        self.assertIn('KAZUMA PORT GAMES BR',data)

if __name__=='__main__':unittest.main()
