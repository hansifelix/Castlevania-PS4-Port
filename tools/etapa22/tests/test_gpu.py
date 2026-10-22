from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audit22',ROOT/'auditar_gpu.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class TestAuditoriaGPU(unittest.TestCase):
    def test_ignora_comentarios(self):
        vals = audit.scan_text({'a.cpp': '// vkCreateFake(\n/*vkCreateHidden*/\n vkCreateInstance();'})
        self.assertEqual(set(vals), {'vkCreateInstance'})
    def test_nvn_incompleto_recusado(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):audit.analyze(Path(d),Path(d))
    def test_variantes_sdk_nao_provam_port(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'nvn').mkdir(); (p/'sdk/include/vulkan').mkdir(parents=True)
            (p/'sdk/include/vulkan/vulkan.h').write_text('Vulkan')
            (p/'nvn/nvn_vk.cpp').write_text('vkCreateInstance();vkCreateDevice();vkQueuePresentKHR();')
            result=audit.analyze(p/'nvn',p/'sdk')
            self.assertTrue(result['openorbis_base_contem_header_vulkan_h'])
            self.assertFalse(result['motor_castlevania_testado'])
            self.assertEqual(result['go_no_go'],'INDETERMINADO')
    def test_render_reconhece_limites(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'nvn').mkdir();(p/'sdk').mkdir()
            (p/'nvn/nvn_vk.cpp').write_text('vkCreateInstance();vkCreateDevice();vkQueuePresentKHR();')
            result=audit.analyze(p/'nvn',p/'sdk')
            s=audit.render(result)
            self.assertIn('INDETERMINADO',s)
            self.assertIn('Nenhum ELF, PKG',s)

if __name__=='__main__':unittest.main()
