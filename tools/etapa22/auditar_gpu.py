#!/usr/bin/env python3
"""Inventario estatico parcial de entrada NVN/Vulkan, sem executar codigo comercial."""
import argparse
import json
import re
from pathlib import Path

CATEGORIES = {
    'criacao_dispositivos': ('vkGetInstanceProcAddr', 'vkCreateInstance', 'vkEnumeratePhysicalDevices', 'vkCreateDevice'),
    'comandos_sincronizacao': ('vkBeginCommandBuffer', 'vkEndCommandBuffer', 'vkQueueSubmit', 'vkWaitForFences'),
    'apresentacao': ('vkCreateSwapchainKHR', 'vkAcquireNextImageKHR', 'vkQueuePresentKHR'),
    'recursos_pipelines': ('vkCreateGraphicsPipelines', 'vkCreateComputePipelines', 'vkCreateImage', 'vkCreateBuffer'),
}

def strip_comments(s: str) -> str:
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    return re.sub(r'//[^\n]*', '', s)

def scan_text(name_to_text: dict) -> dict:
    if not name_to_text:
        raise ValueError('nenhum arquivo NVN fornecido')
    funcs = {}
    for filename, raw in sorted(name_to_text.items()):
        # APENAS ocorrencias textuais, nao garantem chamadas realmente ligadas.
        for fn in set(re.findall(r'\bvk[A-Z][A-Za-z0-9_]*\b', strip_comments(raw))):
            funcs.setdefault(fn, []).append(filename)
    return {k: sorted(v) for k,v in sorted(funcs.items())}

def analyze(folder: Path, sdk: Path) -> dict:
    source_files=sorted(folder.glob('*.cpp')) + sorted(folder.glob('*.h'))
    if not source_files or not (folder/'nvn_vk.cpp').is_file():
        raise ValueError('pasta nvn incompleta ou ausente')
    sources={str(f.relative_to(folder)):f.read_text(encoding='utf-8',errors='replace') for f in source_files}
    funcs=scan_text(sources)
    if not {'vkCreateInstance','vkCreateDevice','vkQueuePresentKHR'} <= set(funcs):
        raise ValueError('NVN sem pontos esperados; revisar upstream antes de tirar conclusoes')
    header_list=list(sdk.glob('include/**/vulkan.h'))
    lib_list=sorted([str(f.relative_to(sdk)) for f in sdk.glob('lib/**/*vulkan*') if f.is_file()])
    categories={category: {'encontradas': [fn for fn in names if fn in funcs],
                           'nao_identificadas_nesta_varredura': [fn for fn in names if fn not in funcs]}
                for category,names in CATEGORIES.items()}
    return {
        'etapa':22, 'tipo':'auditoria_estatica_parcial_NVNVulkan',
        'arquivos_nvn_analisados':len(source_files),
        'vulkan_nomes_distintos_achados':len(funcs),
        'vulkan_nomes_e_arquivos':funcs,
        'categorias_priorizadas':categories,
        'openorbis_base_contem_header_vulkan_h':bool(header_list),
        'openorbis_base_contem_biblioteca_nome_vulkan':bool(lib_list),
        'openorbis_bibliotecas_nome_vulkan':lib_list,
        'projetos_terceiros_para_investigar':[
            'https://github.com/orbis-ports/mesa-ps4',
            'https://github.com/PS4-OpenGNM/vulkan-ps4'],
        'versao_vulkan_efetiva_PS4':'NAO_VERIFICADA',
        'backend_vulkan_em_execucao_ps4':'NAO_TESTADO',
        'suporte_EXT_formato_shader':'NAO_VERIFICADO',
        'motor_castlevania_testado':False,
        'go_no_go':'INDETERMINADO',
        'observacao':'Presenca de vk* nos arquivos e de bibliotecas no SDK NAO demonstra execucao nem compatibilidade com o PS4.'}

def render(x: dict) -> str:
    lines = ['# Kazuma Etapa 22 — diagnóstico GPU (somente estático)', '',
        '**Ainda não foi determinado se o port gráfico funciona no PS4.**', '',
        f"Arquivos NVN examinados: **{x['arquivos_nvn_analisados']}**. Nomes distintos `vk*`: **{x['vulkan_nomes_distintos_achados']}**.",
        '', 'A contagem é textual/parcial, não representa o conjunto completo de chamadas efetivas.', '',
        '| Sinal no SDK OpenOrbis v0.5.4 | Encontrado |', '|---|---|',
        f"| header `vulkan.h` | {'Sim' if x['openorbis_base_contem_header_vulkan_h'] else 'Nao'} |",
        f"| biblioteca com nome `vulkan` | {'Sim' if x['openorbis_base_contem_biblioteca_nome_vulkan'] else 'Nao'} |",
        '', '| Grupo | Identificadas no fonte | Outras na amostra não identificadas |', '|---|---|---|']
    for group,v in x['categorias_priorizadas'].items():
        lines.append(f"| {group} | {', '.join(v['encontradas']) or '—'} | {', '.join(v['nao_identificadas_nesta_varredura']) or '—'} |")
    lines += ['', '## Alternativas públicas a estudar (NÃO verificadas no PS4 do usuário)', '',
        '- [orbis-ports/mesa-ps4](https://github.com/orbis-ports/mesa-ps4) — RADV adaptado para PS4.',
        '- [PS4-OpenGNM/vulkan-ps4](https://github.com/PS4-OpenGNM/vulkan-ps4) — proposta de Vulkan sobre GNM.',
        '', 'Essas fontes não provam a compatibilidade exigida pelo NVN nem versão/extensões realmente disponíveis.',
        '', '## Faltam provas', '',
        '- Integrar e inicializar backend Vulkan real no console e ler propriedades da GPU.',
        '- Testar extensão/swapchain/superfícies, formatos, shaders, apresentação e memória.',
        '- Resolver recompilação dos módulos reais, HLE e mapa de memória do jogo.',
        '', '**Resultado técnico: INDETERMINADO.** Nenhum ELF, PKG ou arquivo do jogo foi gerado.', '']
    return '\n'.join(lines).replace('\\n','\n')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--nvn',type=Path,required=True);p.add_argument('--sdk',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); x=analyze(a.nvn,a.sdk);a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'gpu_dependencias.json').write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (a.out/'GPU_DIAGNOSTICO.md').write_text(render(x),encoding='utf-8')
    print(f"ETAPA 22: {x['arquivos_nvn_analisados']} fontes NVN; {x['vulkan_nomes_distintos_achados']} nomes vk; PS4 NAO TESTADO; sem PKG.")
if __name__=='__main__':main()
