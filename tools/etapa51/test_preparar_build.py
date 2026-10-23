from pathlib import Path
import unittest,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from preparar_build import derive

# Check against the committed base builder in the user repo; no SDK needed.
class BuildTests(unittest.TestCase):
    def test_builder(self):
        p=Path('tools/etapa13/compilar_homebrew_pkg.sh')
        if not p.is_file():self.skipTest('Run in repository root')
        s=derive(p.read_text(encoding='utf-8'))
        for word in ('tools/etapa50/platform_ps4_memory.cpp','"$scratch/memory.o"',
                     'BREW95108','KAZUMA51MEM00000','release/etapa51'):
            self.assertIn(word,s)
        self.assertNotIn('tools/etapa13/tela_kazuma.cpp',s)
        self.assertNotIn('KAZUMAPADTEST000',s)
    def test_safety(self):
        p=Path('tools/etapa51/tela_kazuma.cpp')
        if not p.is_file():p=Path(__file__).resolve().parent/'tela_kazuma.cpp'
        s=p.read_text(encoding='utf-8')
        for required in ('nx::plat::reserve(', 'nx::plat::commit(', 'nx::plat::decommit(',
                         'KAZUMA51:','0x4000000000ULL','0x4010000000ULL','0x4020000000ULL'):
            self.assertIn(required,s)
        self.assertNotIn('MAP_FIXED |',s)  # no forced mappings
        self.assertNotIn('reinterpret_cast<volatile unsigned char*>(addr)[0]',s)
        self.assertIn('if (r.commit_ok)',s)
if __name__=='__main__':unittest.main()
