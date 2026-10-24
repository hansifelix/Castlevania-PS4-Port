import unittest
from gerar_workflow import generate

class Tests(unittest.TestCase):
    @staticmethod
    def baseline():
        return """name: 'Kazuma Etapa 73 - contrato input Vulkan PS4 (SEM JOGO / SEM PKG)'
on:
  pull_request:
    paths:
      - 'tools/etapa73/**'
      - name: Integrar read_pad + tres APIs Vulkan reais ao nx boot (SEM JOGO)
        run: |
          set -euo pipefail
          bash tools/etapa73/integrar.ps4.sh
      - name: Publicar arquivos
        with:
          name: kazuma-etapa73-input-vulkan-sem-jogo
"""
    def test_generate_keeps_baseline(self):
        s=generate(self.baseline())
        assert 'bash tools/etapa73/integrar.ps4.sh' in s
        assert 'bash tools/etapa74/integrar_videoout.sh' in s
        assert "'tools/etapa74/**'" in s
        assert 'kazuma-etapa74-videoout-sem-jogo' in s
    def test_reject_missing_anchors(self):
        with self.assertRaises(AssertionError): generate('empty')
