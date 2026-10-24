import unittest
from avaliar import nm,analyze
class Tests(unittest.TestCase):
    def test_weak(self):
        self.assertEqual(nm('  U sceAudioOutInit\n  w symbol\n')[0],{'sceAudioOutInit'})
    def test_three_functions(self):
        b={'nx::plat::audio_open(void (*)(void*))',
           'nx::plat::audio_submit(void const*, unsigned long, void*)',
           'nx::plat::audio_queued()', 'nx_module_main'}
        a={'sceAudioOutInit','sceAudioOutOpen','sceAudioOutOutput','nx_module_main'}
        d='\n'.join('T '+x for x in b)
        o=analyze(b,a,d,{'sceAudioOutInit','sceAudioOutOpen','sceAudioOutOutput'},'FALHOU_LINK_ESTRITO')
        self.assertEqual(o['apis_audio_resolvidas'],3)
        self.assertEqual(o['nx_plat_pendente'],[])
        self.assertFalse(o['pkg_gerado'])
    def test_missing_import_fails(self):
        b={'nx::plat::audio_open(a)', 'nx::plat::audio_submit(a)', 'nx::plat::audio_queued()'}
        with self.assertRaises(ValueError):analyze(b,{},'\n'.join('T '+x for x in b),{'sceAudioOutOpen'},'NO')
if __name__=='__main__':unittest.main()
