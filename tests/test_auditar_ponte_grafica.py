import unittest
from tools.auditar_ponte_grafica import audit, extracted_additions, markdown_report, CALLBACKS


def patch_with(platform_source, wsi_source):
    return ('diff --git a/runtime/src/platform_ps4.cpp b/runtime/src/platform_ps4.cpp\n'
            '+++ b/runtime/src/platform_ps4.cpp\n' +
            '\n'.join('+' + line for line in platform_source.splitlines()) + '\n'
            'diff --git a/runtime/src/ps4/ps4_vk_wsi.cpp b/runtime/src/ps4/ps4_vk_wsi.cpp\n'
            '+++ b/runtime/src/ps4/ps4_vk_wsi.cpp\n' +
            '\n'.join('+' + line for line in wsi_source.splitlines()) + '\n')


class GraphicsAuditTests(unittest.TestCase):
    def test_extraction_only_target_added_lines(self):
        p = patch_with('void vulkan_get_instance_proc_addr() {}',
                       'namespace nx::plat::ps4 {}')
        self.assertIn('vulkan_get_instance_proc_addr', extracted_additions(p, 'runtime/src/platform_ps4.cpp'))
        self.assertNotIn('namespace nx::plat::ps4', extracted_additions(p, 'runtime/src/platform_ps4.cpp'))

    def test_all_contracts_and_wsi_in_reference(self):
        required = list(CALLBACKS)
        host = '\n'.join(f'void {f}();' for f in required)
        nvn = '\n'.join(f'plat::{f}();' for f in required)
        ps4 = '\n'.join(f'void {f}() {{}}' for f in required)
        ps4 += '\nVK_EXT_HEADLESS_SURFACE_EXTENSION_NAME vkCreateHeadlessSurfaceEXT'
        wsi = ('namespace nx::plat::ps4 {\n'
               'CreateSwapchainKHR QueuePresentKHR\n'
               'sceVideoOutRegisterBuffers sceVideoOutSubmitFlip ac_ps4_submit_flip\n}')
        report = audit(host, nvn, 'set(NX_MODULES main sdk subsdk0)', patch_with(ps4, wsi))
        self.assertTrue(report['critical_source_matches'])
        self.assertIn('NÃO', markdown_report(report))

    def test_missing_wsi_is_not_marked_success(self):
        host = ' '.join(f'void {f}();' for f in CALLBACKS)
        nvn = ' '.join(f'plat::{f}();' for f in CALLBACKS)
        report = audit(host, nvn, 'set(NX_MODULES main sdk)', patch_with(host, ''))
        self.assertFalse(report['critical_source_matches'])
        self.assertIn('wsi.videoout', report['critical_missing'])
        self.assertIn('castlevania.subsdk0', report['critical_missing'])


if __name__ == '__main__':
    unittest.main()
