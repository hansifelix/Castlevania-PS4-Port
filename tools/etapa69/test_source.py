import importlib.util
from pathlib import Path
import unittest

SRC = Path('tools/etapa69/prepare_source.py')

class SourceTests(unittest.TestCase):
    def test_sources_and_shaders_have_real_draw_loop(self):
        draw = Path('tools/etapa69/elephant_draw.h').read_text()
        assert 'scePadReadState' in draw
        assert 'ELEPHANT69_CROSS 0x4000u' in draw
        assert 'vkCmdPushConstants' in draw
        assert 'vkCmdDraw(c, 6, 1, 0, 0)' in draw
        vertex = Path('tools/etapa69/elephant.vert').read_text()
        assert 'layout(push_constant)' in vertex
        assert 'gl_VertexIndex' in vertex
    def test_transformation_on_real_stage68_1(self):
        s1=importlib.util.spec_from_file_location('p68','tools/etapa68/prepare_source.py')
        mod=importlib.util.module_from_spec(s1);s1.loader.exec_module(mod)
        s2=importlib.util.spec_from_file_location('p69',SRC)
        g=importlib.util.module_from_spec(s2);s2.loader.exec_module(g)
        base=Path('tools/etapa67/triangle.c').read_text()
        result=g.patch(mod.patch(base))
        for anchor in ('elephant_scene(cmds[idx]','elephant_pressed_x()',
                       'vkResetCommandBuffer(cmds[idx]', 'VKLOADER_INSTANCE_REGISTRADA=OK',
                       'vkQueuePresentKHR(queue, &pi)', 'ORBIS_SUBMIT_DONE'):
            self.assertIn(anchor,result)
        self.assertNotIn('tri_vert_spv',result)
        self.assertNotIn('tri_frag_spv',result)
        self.assertNotIn('vkCmdDraw(cmds[i], 3, 1, 0, 0)',result)
        self.assertNotIn('must(vkResetCommandBuffer',result)
if __name__=='__main__':unittest.main()
