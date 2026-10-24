import unittest
from gerar_workflow import generate, SOURCE
class Tests(unittest.TestCase):
 def test_reaproveitar_baseline(self):
  src=SOURCE.read_text()
  dst=generate(src)
  assert 'integrar_memoria.sh' in dst
  assert 'integrar_threads.sh' in dst
  assert 'kazuma-etapa71-threads-boot-sem-jogo' in dst
  assert "'tools/etapa71/**'" in dst
if __name__=='__main__':unittest.main()
