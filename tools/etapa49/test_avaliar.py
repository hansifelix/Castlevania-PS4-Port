import unittest
from avaliar import avaliar, PREFIXOS

class TesteRelatorio(unittest.TestCase):
    def test_seis_apis_retiram_simbolos_pendentes(self):
        before={x+' TESTE' if x.endswith('(') else x for x in PREFIXOS}
        after={'nx::plat::create_window()', 'nx_module_main'}
        r=avaliar(before,after,'\n'.join(PREFIXOS))
        self.assertEqual(r['apis_basicas_resolvidas'],6)
        self.assertEqual(r['apis_plataforma_pendentes'],1)
        self.assertFalse(r['executou_runtime'])
    def test_falha_se_pendente_continua(self):
        before={x+' TESTE' if x.endswith('(') else x for x in PREFIXOS}
        with self.assertRaisesRegex(ValueError,'AINDA indefinida'):
            avaliar(before,before,'\n'.join(PREFIXOS))
    def test_falha_sem_definicao(self):
        before={x+' TESTE' if x.endswith('(') else x for x in PREFIXOS}
        with self.assertRaisesRegex(ValueError,'nao definida'):
            avaliar(before,set(),'')

if __name__=='__main__': unittest.main()
