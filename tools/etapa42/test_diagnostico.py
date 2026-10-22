import unittest
from diagnosticar_link import unique_errors


class TestarErros(unittest.TestCase):
    def test_agrupamento_e_deduplicacao(self):
        log = '''ld.lld-18: error: undefined symbol: nx::plat::criar()
>>> referenced by foo.o
ld.lld-18: error: undefined symbol: nx::plat::criar()
ld.lld-18: error: duplicate symbol: main
ld.lld-18: error: unable to find library -lexemplo
ld.lld-18: error: relocation R_X86_64_32 cannot be used
'''
        r = unique_errors(log)
        self.assertEqual(r['simbolos_indefinidos'], ['nx::plat::criar()'])
        self.assertEqual(r['simbolos_duplicados'], ['main'])
        self.assertEqual(r['bibliotecas_ausentes'], ['-lexemplo'])
        self.assertEqual(len(r['outros_erros']), 1)

    def test_log_sem_erros(self):
        r = unique_errors('Link OK\n')
        self.assertTrue(all(not x for x in r.values()))


if __name__ == '__main__':
    unittest.main()
