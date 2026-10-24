import unittest
from gerar_workflow import generate
class Tests(unittest.TestCase):
  def test_reuso_74(self):
    old="name: 'Kazuma Etapa 74 - display VideoOut nx runtime PS4 (SEM JOGO / SEM PKG)'"
    art='name: kazuma-etapa74-videoout-sem-jogo'
    path="      - 'tools/etapa74/**'"
    anchor="""      - name: Integrar seis APIs reais VideoOut ao boot (SEM JOGO)
        run: |
          set -euo pipefail
          bash tools/etapa74/integrar_videoout.sh
"""
    text=old+'\n'+path+'\n'+anchor+'\n'+art
    s=generate(text)
    self.assertIn('tools/etapa75/integrar_audio.sh',s)
    self.assertIn('name: kazuma-etapa75-audioout-sem-jogo',s)
    self.assertEqual(s.count('tools/etapa74/integrar_videoout.sh'),1)
  def test_fail_closed(self):
    with self.assertRaises(AssertionError): generate('bad')
if __name__=='__main__':unittest.main()
