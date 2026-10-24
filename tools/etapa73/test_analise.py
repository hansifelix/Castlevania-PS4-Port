import unittest
from avaliar import analyze,sym
from gerar_workflow import generate
class Tests(unittest.TestCase):
 def test_symbols(self):
  self.assertEqual(sym('  U foo\n  w opcional\n'),{'foo'})
 def test_contract(self):
  targets=['nx::plat::read_pad(nx::plat::PadState&)','nx::plat::vulkan_get_instance_proc_addr()','nx::plat::vulkan_surface_extension()','nx::plat::vulkan_create_surface(void*, void*, unsigned long*, void*)']
  before=set(targets)|{'nx_module_main'}
  after={'nx_module_main','vkGetInstanceProcAddr','scePadReadState'}
  defs='\n'.join('T '+q for q in targets)
  res=analyze(before,after,defs,'FALHOU_LINK_ESTRITO')
  self.assertEqual(res['api_implementadas'],4)
  self.assertFalse(res['pkg_gerado'])
 def test_reject_unresolved(self):
  before={'nx::plat::read_pad(nx::plat::PadState&)' }
  with self.assertRaises(ValueError):analyze(before,before,'','FALHOU')
 def test_gen(self):
  original="""name: 'Kazuma Etapa 72 - scePthread nativo PS4 (SEM JOGO / SEM PKG)'\non:\n  pull_request:\n    paths:\n      - 'tools/etapa72/**'\n      - name: Integrar 5 APIs threads PS4 com scePthread e tentar link ESTRITO\n        run: |\n          set -euo pipefail\n          bash tools/etapa72/integrar_threads_nativas.sh\nname: kazuma-etapa72-sce-pthread-sem-jogo\n"""
  out=generate(original)
  self.assertIn('tools/etapa73',out)
  self.assertIn('integrar.ps4.sh',out)
if __name__=='__main__':unittest.main()
