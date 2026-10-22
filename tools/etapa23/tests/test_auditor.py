import unittest,importlib.util
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'auditar.py'
spec=importlib.util.spec_from_file_location('audit23',p)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def fixture():
 return {'nvn':'app.apiVersion = VK_API_VERSION_1_3;',
         'draw':'p_vkCmdBeginRendering(a, b); p_vkCmdEndRendering(a);',
         'exports':'VKAPI_CALL vkCreateInstance(\n VKAPI_CALL vkCreateDevice(',
         'header':'#define VK_PS4_API_VERSION VK_MAKE_VERSION(1, 1, 0)',
         'readme':'Vulkan 1.0 ICD',
         'mesa_build':'needs orbis-compat and orbis-porting-kit'}
class AuditTests(unittest.TestCase):
 def test_detecta_incompatibilidade(self):
  x=a.analyze(fixture());self.assertEqual(x['runtime_vulkan'],'1.3')
  self.assertEqual(x['backend_header_vulkan'],'1.1.0')
  self.assertIn('vkCmdBeginRendering',x['nao_encontrados_em_exports'])
 def test_sem_prova_do_console(self):
  x=a.analyze(fixture());self.assertFalse(x['console_testado']);self.assertFalse(x['pkg_gerado'])
  self.assertIn('INDETERMINADA',x['viabilidade_castlevania'])
 def test_rejeita_fonte_ausente(self):
  with self.assertRaises(ValueError):a.analyze({'nvn':'test'})
 def test_rejeita_mudanca_runtime(self):
  d=fixture();d['nvn']='app.apiVersion = VK_API_VERSION_1_2;'
  with self.assertRaises(ValueError):a.analyze(d)
if __name__=='__main__':unittest.main()
