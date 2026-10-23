import unittest
from avaliar import TARGETS,analyze

class TesteRelatorio(unittest.TestCase):
    def test_tres_simbolos_removidos(self):
        pre={t+'dummy)' for t in TARGETS}|{'nx::plat::audio_open(dummy)'}
        post={'nx::plat::audio_open(dummy)','mprotect','mmap'}
        d=analyze(pre,post,'\n'.join(TARGETS),'FALHOU_LINK_ESTRITO')
        self.assertEqual(d['apis_memoria_resolvidas'],3)
        self.assertEqual(d['plataforma_pendente'],1)
        self.assertFalse(d['memoria_ps4_testada_no_hardware'])
    def test_rejeita_pendencia(self):
        pre={t+'dummy)' for t in TARGETS}
        with self.assertRaisesRegex(ValueError,'Ainda indefinido'):
            analyze(pre,pre,'\n'.join(TARGETS),'FALHOU_LINK_ESTRITO')
    def test_rejeita_sem_simbolo(self):
        pre={t+'dummy)' for t in TARGETS}
        with self.assertRaisesRegex(ValueError,'Objeto nao definiu'):
            analyze(pre,set(),'', 'FALHOU_LINK_ESTRITO')

if __name__=='__main__':unittest.main()
