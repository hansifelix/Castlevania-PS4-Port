import unittest
from gerar_workflow import derive
class TesteGerador(unittest.TestCase):
    def test_blocos_novos(self):
        s=("name: 'Kazuma Etapa 49 - ligar 6 APIs host ao boot runtime PS4 (SEM JOGO / SEM PKG)'\n"
           "      - '.github/workflows/kazuma-etapa49-host-basics.yml'\n"
           'name: kazuma-etapa49-delta-dependencias-boot-real-sem-pkg\n'
           '      - name: Publicar diagnosticos SEM artefatos comerciais ou PKG\n')
        d=derive(s)
        self.assertIn('tools/etapa50/integrar_memoria.sh',d)
        self.assertIn('tools/etapa50/**',d)
        self.assertIn('Etapa 50 - memoria virtual',d)
if __name__=='__main__':unittest.main()
