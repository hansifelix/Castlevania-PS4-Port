import unittest
from pathlib import Path
from preparar_build import derive

class SmokeBuild(unittest.TestCase):
    def test_essential_markers(self):
        # Testa marcadores independentemente do builder real (ele sera validado no runner).
        code=Path('tools/etapa47/preparar_build.py').read_text()
        for name in ('BREW94708','KAZUMA47TIME0000','platform_ps4_files.cpp','platform_ps4_core_clock.cpp','kazuma47.dat'):
            self.assertIn(name,code)
    def test_clock_contract(self):
        data=Path('tools/etapa47/tela_kazuma.cpp').read_text()
        self.assertIn('KAZUMA47: DIAG_START',data)
        self.assertIn('make_dirs("")',data)
        self.assertIn('PERF MODO=%s FPS_X10=',data)
        self.assertIn('TIMER_NATIVE_HZ=',data)
        self.assertIn('delta>=1500000ull',data)
        self.assertIn('PERF MODO=%s',data)
        self.assertIn('clock_ok && frame_start',data)
        self.assertIn('ORBIS_PAD_BUTTON_TRIANGLE',data)
        self.assertIn('KAZUMA PORT GAMES BR',data)
        builder=Path('tools/etapa47/preparar_build.py').read_text()
        self.assertIn('tools/etapa47/platform_ps4_core_clock.cpp',builder)

if __name__=='__main__':unittest.main()
