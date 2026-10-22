import unittest
from avaliar_link import avaliar

class AvaliarLink(unittest.TestCase):
    def test_simbolos_distintos(self):
        v=avaliar('ld.lld: error: undefined symbol: abc\nld.lld: error: undefined symbol: abc\nld.lld: error: undefined symbol: xyz', 'FALHOU',True)
        self.assertEqual(v['quantidade_simbolos_no_log'],2)
        self.assertEqual(v['simbolos_nao_resolvidos_no_log'],['abc','xyz'])
    def test_sem_symbols(self):
        self.assertEqual(avaliar('', 'ELF_INTERMEDIARIO', True)['quantidade_simbolos_no_log'],0)

if __name__=='__main__':unittest.main()
