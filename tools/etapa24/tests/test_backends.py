import importlib.util
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'auditar_backends.py'
spec=importlib.util.spec_from_file_location('audit24',P)
a=importlib.util.module_from_spec(spec); spec.loader.exec_module(a)

def fixtures():
    return {
      'runtime_device':'app.apiVersion = VK_API_VERSION_1_3; /* vkFake */',
      'runtime_draw':'p_vkCmdBeginRendering(cb, &ri); p_vkCmdEndRendering(cb);',
      'gnm_header':'#define VK_PS4_API_VERSION VK_MAKE_VERSION(1,1,0)',
      'gnm_exports':'VKAPI_CALL vkCreateInstance(\n VKAPI_CALL vkCreateDevice(',
      'mesa_radv':'.apiVersion = pdev->info.gfx_level >= GFX8 ? RADV_API_VERSION : RADV_API_VERSION_1_3,',
      'mesa_wsi':'#if defined(__PS4__)\nsceVideoOutRegisterBuffers();sceVideoOutSubmitFlip();\n#endif',
      'mesa_readme':'libvulkan_radeon.a ; link probe',
      'mesa_build':'orbis-compat liborbis-compat.a',
      'mesa_entrypoint':'orbis-porting-kit'
    }
class TestEtapa24(unittest.TestCase):
    def test_identifica_contrato_real(self):
        r=a.analyze(fixtures())
        self.assertEqual(r['runtime_vulkan'],'1.3')
        self.assertEqual(r['opengnm_header_vulkan'],'1.1.0')
        self.assertEqual(set(r['opengnm_dynamic_rendering_ausente_neste_arquivo_de_exports']),{'vkCmdBeginRendering','vkCmdEndRendering'})
    def test_gfx7_declarado_sem_promessa_de_console(self):
        r=a.analyze(fixtures())
        self.assertTrue(r['mesa_radv_gfx7_declara_vulkan_1_3'])
        self.assertFalse(r['mesa_testada_no_PS4_do_usuario'])
        self.assertEqual(r['port_completo_viavel'],'INDETERMINADO')
    def test_rejeita_registro_sem_evidencia_de_gfx7(self):
        f=fixtures();f['mesa_radv']='.apiVersion = RADV_API_VERSION;'
        with self.assertRaises(ValueError):a.analyze(f)
    def test_rejeita_fonte_incompleta(self):
        with self.assertRaises(ValueError):a.analyze({'runtime_device':'hello'})
    def test_relatorio_limita_conclusoes(self):
        s=a.report(a.analyze(fixtures()))
        self.assertIn('hipotese de integracao',s)
        self.assertIn('Nenhum codigo comercial, arquivo de jogo ou PKG',s)
if __name__=='__main__':unittest.main()
