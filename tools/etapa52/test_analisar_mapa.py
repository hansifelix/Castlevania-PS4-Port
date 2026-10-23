import copy
import importlib.util
import json
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('audit52',Path(__file__).parent/'analisar_mapa.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
MANIFEST=Path(__file__).parent/'build_publico_1_1_0.json'
class TestMap(unittest.TestCase):
    def setUp(self):self.m=json.loads(MANIFEST.read_text())
    def test_proves_floor_not_full(self):
        result=a.audit(self.m)
        self.assertEqual(len(result['modulos']),3)
        self.assertTrue(all(not m['mapa_completo'] for m in result['modulos']))
        self.assertGreater(result['piso_intervalo_modulos_mib'],512)
        self.assertEqual(result['pagina_observada_etapa51_bytes'],16384)
    def test_wrong_version_rejected(self):
        self.m['content_version']='1.3.2'
        with self.assertRaises(ValueError):a.audit(self.m)
    def test_overlap_rejected(self):
        self.m['modules'][1]['image_bytes']=350*1024*1024
        with self.assertRaises(ValueError):a.audit(self.m)
    def test_alignment_and_host(self):
        self.assertEqual(a.round_up(16385,16384),32768)
        self.assertGreater(a.audit(self.m)['host_total_virtual_reservado_gib'],70)
if __name__=='__main__':unittest.main()
