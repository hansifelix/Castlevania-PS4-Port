import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[3]

class TestPacote(unittest.TestCase):
    def test_codigo_sintetico(self):
        p=(ROOT/'tools/etapa20/cpu_probe.cpp').read_text()
        self.assertIn('#include <nx/cpu.h>',p)
        self.assertIn('nx::CPU',p)
        self.assertIn('nx::st<std::uint64_t>',p)
        self.assertIn('nx::ld<std::uint64_t>',p)
    def test_sem_pkg_e_sem_execucao_console(self):
        flow=(ROOT/'.github/workflows/kazuma-etapa20-cpu-gate.yml').read_text()
        build=(ROOT/'tools/etapa20/testar_cpu_guest_openorbis.sh').read_text()
        self.assertNotIn('pkg_build',flow+build)
        self.assertNotIn('create-fself',flow+build)
        self.assertIn("'gerou_pkg':False",build)
        self.assertIn("'executado_no_ps4':False",build)
    def test_commits_fixos(self):
        flow=(ROOT/'.github/workflows/kazuma-etapa20-cpu-gate.yml').read_text()
        self.assertIn('4043f21bb4f656d34cd17ba070238c7728d00631',flow)
        self.assertIn('3c7cd5bb593ca74fa1c13fd59f3938dc0fc07985167f7275063019e63abe4526',flow)
    def test_nao_confundir_objeto_com_port(self):
        doc=(ROOT/'docs/KAZUMA_ETAPA20_CPU_GATE.md').read_text()
        self.assertIn('nao e possivel prometer',doc)
        self.assertIn('sintetico',doc)

if __name__=='__main__': unittest.main()
