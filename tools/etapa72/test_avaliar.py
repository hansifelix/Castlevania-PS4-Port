import unittest
from avaliar import TARGETS, IMPORTS, undefined_nm, audit

class Tests(unittest.TestCase):
    def test_simbolos_fracos_nao_sao_indefinidos_obrigatorios(self):
        u,w=undefined_nm('                 U nx::plat::yield()\n                 w opcional\n                 v opcional2\n')
        self.assertEqual(u,{'nx::plat::yield()'})
        self.assertEqual(len(w),2)

    def test_cinco_funcoes_e_backend_nativo(self):
        before={x+'assinatura)' if x.endswith('(') else x for x in TARGETS} | {'nx_module_main'}
        after={'nx_module_main','scePthreadCreate','scePthreadRename'}
        definitions='\n'.join('T '+x for x in before if x.startswith('nx::plat::'))
        r=audit(before,after,definitions,set(IMPORTS),'FALHOU_LINK_ESTRITO')
        self.assertEqual(r['api_implementadas'],5)
        self.assertEqual(len(r['modulos_do_jogo_pendentes']),1)
        self.assertFalse(r['gerou_pkg'])

    def test_recusa_imports_posix_ao_ps4(self):
        before={x+'assinatura)' if x.endswith('(') else x for x in TARGETS}
        definitions='\n'.join('T '+x for x in before)
        with self.assertRaisesRegex(ValueError,'pthread POSIX'):
            audit(before,set(),definitions,set(IMPORTS)|{'pthread_create'},'FALHOU_LINK_ESTRITO')

if __name__=='__main__': unittest.main()
