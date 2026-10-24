import unittest
from pathlib import Path
from prepare_source import patch


class Etapa68Tests(unittest.TestCase):
    def test_transforma_renderizador_real_sem_alterar_original(self):
        src = Path('tools/etapa67/triangle.c').read_text(encoding='utf-8')
        result = patch(src)
        self.assertIn('kazuma68_create_surface(instance, &surface)', result)
        self.assertIn('get_proc(VK_NULL_HANDLE, "vkCreateInstance")', result)
        # Regressao real: ICD direto nao inicializa g_instance no ps4-vkloader.
        self.assertIn('must(vkCreateInstance(&ici, NULL, &instance), "vkCreateInstance(ps4-vkloader)")', result)
        self.assertNotIn('must(create_instance(&ici, NULL, &instance)', result)
        self.assertIn('VKLOADER_INSTANCE_REGISTRADA=OK', result)
        self.assertIn('vkQueuePresentKHR(queue, &pi)', result)
        self.assertIn('ORBIS_SUBMIT_DONE', result)
        self.assertNotIn('vkCreateHeadlessSurfaceEXT(instance, &hsci, NULL, &surface)', result)
        self.assertIn('NX_PLAT_SURFACE=OK', result)
        self.assertIn('KAZUMA68: frame', result)

    def test_recusa_silenciosamente_mudar_anchors_nao(self):
        with self.assertRaises(ValueError):
            patch('unexpected new renderer')

if __name__ == '__main__':
    unittest.main()
