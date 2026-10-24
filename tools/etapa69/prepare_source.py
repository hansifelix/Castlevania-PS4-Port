#!/usr/bin/env python3
"""Transform an Etapa 68.1 GPU-tested source into the Elephant Runner.
All changes limited to rendering loop, shader binding, and controller polling.
Never silently accept a changed upstream anchor.
"""
from pathlib import Path
import re
import sys

def replace_once(text, before, after):
    n=text.count(before)
    if n != 1:
        raise RuntimeError(f'Esperava UMA ancora, encontrei {n}: {before[:110]!r}')
    return text.replace(before, after, 1)

def patch(text):
    if 'VKLOADER_INSTANCE_REGISTRADA=OK' not in text:
        raise RuntimeError('Etapa 68.1 hotfix ausente — faca merge na PR 57 antes.')
    # Replace both generated header names AND the SPIR-V uint32_t array symbols.
    if text.count('tri_vert_spv') < 2 or text.count('tri_frag_spv') < 2:
        raise RuntimeError('Shader symbols of Etapa 67 changed unexpectedly')
    text = text.replace('tri_vert_spv', 'elephant_vert_spv')
    text = text.replace('tri_frag_spv', 'elephant_frag_spv')
    text=replace_once(text, 'int main(void)', '#include "elephant_draw.h"\n\nint main(void)')
    text=replace_once(text,
        'VkPipelineLayoutCreateInfo plci = { .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO };',
        'VkPushConstantRange pc_range = { .stageFlags = VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,\n'
        '        .offset = 0, .size = sizeof(ElephantSprite) };\n'
        '    VkPipelineLayoutCreateInfo plci = { .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,\n'
        '        .pushConstantRangeCount = 1, .pPushConstantRanges = &pc_range };')
    text=replace_once(text,
        '.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO, .queueFamilyIndex = qf,',
        '.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,\n'
        '        .queueFamilyIndex = qf, .flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,')
    # Entire static Etapa67 initial command buffer recording is replaced. Per image re-record below.
    p=re.compile(r'    for \(uint32_t i = 0; i < nimg; i\+\+\) \{\s*VkCommandBufferBeginInfo bi.*?\n    \}\n\n    VkSemaphoreCreateInfo semci',re.S)
    if len(p.findall(text))!=1:
        raise RuntimeError('Nao encontrei o bloco de command buffers estaticos exatamente uma vez.')
    text=p.sub('    /* Comandos sao gravados dinamicamente apos cada acquire. */\n\n    VkSemaphoreCreateInfo semci',text,count=1)
    text=replace_once(text,
        '    say("KAZUMA68: PRESENTACAO_CONTINUA_INICIADA");',
        '    elephant_reset(&elephant_game);\n'
        '    elephant_pad_start();\n'
        '    say("KAZUMA69: ELEFANTE_NA_SELVA; APERTE_X_PARA_PULAR");\n'
        '    say("KAZUMA68: PRESENTACAO_CONTINUA_INICIADA");')
    text=replace_once(text,
        '        VkPipelineStageFlags wait = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;',
        '        /* Atualiza simulacao e entrada antes de gerar o quadro adquirido. */\n'
        '        int cross = elephant_pressed_x();\n'
        '        ElephantEvents ev = elephant_step(&elephant_game, 1.0f/60.0f, cross);\n'
        '        if (ev.jumped) say("KAZUMA69: PULO_X altura_inicial=0");\n'
        '        if (ev.cleared_fence) say("KAZUMA69: CERCA_SUPERADA total=%u", elephant_game.cleared);\n'
        '        if (ev.hit_fence) say("KAZUMA69: COLIDIU_CERCA total=%u", elephant_game.hits);\n'
        '        must(vkResetCommandBuffer(cmds[idx], 0), "vkResetCommandBuffer");\n'
        '        VkCommandBufferBeginInfo bi = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO };\n'
        '        must(vkBeginCommandBuffer(cmds[idx], &bi), "vkBeginCommandBuffer");\n'
        '        VkClearValue clear = { .color = { .float32 = { .38f, .73f, .90f, 1.f } } };\n'
        '        VkRenderPassBeginInfo rpbi = {\n'
        '           .sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,\n'
        '           .renderPass = rp, .framebuffer = fbs[idx],\n'
        '           .renderArea = { {0,0}, extent },\n'
        '           .clearValueCount = 1, .pClearValues = &clear };\n'
        '        vkCmdBeginRenderPass(cmds[idx], &rpbi, VK_SUBPASS_CONTENTS_INLINE);\n'
        '        vkCmdBindPipeline(cmds[idx], VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);\n'
        '        elephant_scene(cmds[idx], layout, &elephant_game);\n'
        '        vkCmdEndRenderPass(cmds[idx]);\n'
        '        must(vkEndCommandBuffer(cmds[idx]), "vkEndCommandBuffer");\n'
        '        VkPipelineStageFlags wait = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;')
    # Must() logs too many per frame: replace dynamic error checking with only failure logging.
    for name in ['vkResetCommandBuffer','vkBeginCommandBuffer','vkEndCommandBuffer']:
        text=replace_once(text, f'must({name}(cmds[idx], '+('0' if name=='vkResetCommandBuffer' else '&bi' if name=='vkBeginCommandBuffer' else '')+f'), "{name}");' if name != 'vkEndCommandBuffer' else f'must({name}(cmds[idx]), "{name}");',
           (f'if ({name}(cmds[idx], '+('0' if name=='vkResetCommandBuffer' else '&bi')+f') != VK_SUCCESS) {{ say("KAZUMA69: ERRO_{name}"); break; }}' if name!='vkEndCommandBuffer' else 'if (vkEndCommandBuffer(cmds[idx]) != VK_SUCCESS) { say("KAZUMA69: ERRO_END_CMD"); break; }'))
    text=text.replace('KAZUMA68:', 'KAZUMA69:')
    if 'vkCreateInstance(ps4-vkloader)' not in text:
        raise RuntimeError('Correcao do loader perdida!')
    if 'vkCmdDraw(c, 6, 1, 0, 0)' in text:
        raise RuntimeError('game draw deve ser compilado no header, nao duplicado')
    return text

def main():
    if len(sys.argv)!=3: raise SystemExit('uso: prepare_source.py SOURCE68_1.c ELEPHANT69.c')
    src=Path(sys.argv[1]).read_text(encoding='utf-8')
    result=patch(src)
    dest=Path(sys.argv[2]);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(result,encoding='utf-8')
    print(f'KAZUMA69: elefante pronto para compilacao; {len(result)} bytes')

if __name__=='__main__':main()
