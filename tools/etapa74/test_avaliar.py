import unittest
from avaliar import TARGETS, undefined, analyze

class Test74(unittest.TestCase):
    def test_nm_weak_ignored(self):
        self.assertEqual(undefined(' U sceVideoOutOpen\n w optional\n U foo\n'), {'sceVideoOutOpen','foo'})
    def test_six_defined_real_but_not_game(self):
        before=set(TARGETS)|{'nx_module_main','old'}
        after={'nx_module_main','sceVideoOutOpen','sceVideoOutGetResolutionStatus','sceVideoOutClose'}
        defined='\n'.join('0000 T '+s for s in TARGETS)
        report=analyze(before,after,defined,'FALHOU_LINK_ESTRITO')
        self.assertEqual(report['apis_videoout_implementadas'],6)
        self.assertFalse(report['game_testado'])
        self.assertEqual(len(report['modulos_jogo_ausentes']),1)
    def test_reject_missing_definition(self):
        with self.assertRaises(AssertionError):
            analyze(set(TARGETS),set(),'T nx::plat::create_window()','FALHOU_LINK_ESTRITO')
    def test_reject_unresolved(self):
        with self.assertRaises(AssertionError):
            analyze(set(TARGETS),{TARGETS[0]},'\n'.join('T '+s for s in TARGETS),'FALHOU_LINK_ESTRITO')
