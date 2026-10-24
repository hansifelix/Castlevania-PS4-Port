import unittest
from avaliar import analyze
class Tests(unittest.TestCase):
    def test_ligacao_concreta_sem_fingir_executavel(self):
        b={'nx::plat::start_thread(void (*)(void*), void*, unsigned long)',
           'nx::plat::exit_thread()','nx::plat::yield()', 'nx_module_main'}
        a={'pthread_create','pthread_exit','sched_yield','nx_module_main'}
        defs='T nx::plat::start_thread(void (*)(void*), void*, unsigned long)\nT nx::plat::exit_thread()\nT nx::plat::yield()\n'
        r=analyze(b,a,defs,'FALHOU_LINK_ESTRITO')
        self.assertEqual(r['apis_thread_definidas'],3)
        self.assertEqual(len(r['modulos_jogo_pendentes']),1)
        self.assertFalse(r['elf_intermediario'])
    def test_recusa_stub_de_funcao_nao_definida(self):
        b={'nx::plat::start_thread(void (*)(void*), void*, unsigned long)',
           'nx::plat::exit_thread()','nx::plat::yield()'}
        with self.assertRaises(ValueError): analyze(b,{},'T nx::plat::yield()', 'FALHOU_LINK_ESTRITO')
if __name__=='__main__':unittest.main()
