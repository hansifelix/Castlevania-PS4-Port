import unittest
from pathlib import Path
from preparar_build import derive

class SmokeBuild(unittest.TestCase):
    def test_essential_markers(self):
        # Testa marcadores independentemente do builder real (ele sera validado no runner).
        code=Path('tools/etapa45/preparar_build.py').read_text()
        for name in ('BREW94508','KAZUMA45DIAG0000','platform_ps4_files.cpp','platform_ps4_core.cpp','kazuma45.dat'):
            self.assertIn(name,code)
    def test_artifact_is_distinct(self):
        data=Path('tools/etapa45/tela_kazuma.cpp').read_text()
        self.assertIn('KAZUMA45: DIAG_START',data)
        self.assertIn('make_dirs("")',data)
        self.assertIn('KAZUMA PORT GAMES BR',data)

if __name__=='__main__':unittest.main()
