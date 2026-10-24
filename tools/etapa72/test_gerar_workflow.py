import unittest
from pathlib import Path
from gerar_workflow import generate
class Tests(unittest.TestCase):
 def test_gera_72_sem_reexecutar_integrador_71(self):
  p=Path('.github/workflows/kazuma-etapa71-runtime-threads.yml')
  if not p.exists():self.skipTest('Teste do workflow requer checkout do repo Kazuma')
  out=generate(p.read_text())
  self.assertIn('integrar_threads_nativas.sh',out)
  self.assertNotIn('bash tools/etapa71/integrar_threads.sh',out)
  self.assertIn('kazuma-etapa72-sce-pthread-sem-jogo',out)
  self.assertIn('KAZUMA_MOCK_PS4',out)
