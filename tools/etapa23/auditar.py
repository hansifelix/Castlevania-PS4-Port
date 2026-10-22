#!/usr/bin/env python3
"""Auditoria estatica Vulkan: apenas fontes publicas, sem PKG ou dados de jogos."""
import argparse, json, re, urllib.request
from pathlib import Path
COMMITS={
 'nx':('SwonDev/cstlvnia-blmont-to-macos','4043f21bb4f656d34cd17ba070238c7728d00631'),
 'gnm':('PS4-OpenGNM/vulkan-ps4','f4d940b723771b3fe637e8ac0704bb5d6ab19622'),
 'mesa':('orbis-ports/mesa-ps4','1a59cc147b54e3970814b37313e2f27357672e9d')}
SOURCES={
 'nvn':('nx','runtime/src/nvn/nvn_vk.cpp'),
 'draw':('nx','runtime/src/nvn/nvn_draw.cpp'),
 'exports':('gnm','src/vk_ps4_entrypoints.c'),
 'header':('gnm','include/vk_ps4_internal.h'),
 'readme':('gnm','README.md'),
 'mesa_build':('mesa','ps4/build.sh')}
def url(key):
    repo,path=SOURCES[key];owner,sha=COMMITS[repo]
    return f'https://raw.githubusercontent.com/{owner}/{sha}/{path}'
def fetch():
    out={}
    for key in SOURCES:
        req=urllib.request.Request(url(key),headers={'User-Agent':'Kazuma-Static-Audit/1.0'})
        with urllib.request.urlopen(req,timeout=25) as r:
            raw=r.read(300001)
            if len(raw)>300000:raise ValueError('Fonte maior que 300KB: '+key)
            out[key]=raw.decode('utf-8-sig')
    return out
def strip_comments(s):
    return re.sub(r'//[^\n]*','',re.sub(r'/\*.*?\*/','',s,flags=re.S))
def analyze(f):
    if set(f)!=set(SOURCES):raise ValueError('Fontes ausentes')
    nvn=strip_comments(f['nvn']); draw=strip_comments(f['draw'])
    hdr=strip_comments(f['header']); ex=strip_comments(f['exports'])
    rt=re.search(r'\bapp\.apiVersion\s*=\s*VK_API_VERSION_(\d+)_(\d+)',nvn)
    bk=re.search(r'#define\s+VK_PS4_API_VERSION\s+VK_MAKE_VERSION\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)',hdr)
    if not rt or not bk:raise ValueError('Formato da versao mudou')
    req=tuple(map(int,rt.groups()));got=tuple(map(int,bk.groups()[:2]))
    if req!=(1,3):raise ValueError('Runtime mudou versao, revisar')
    dynamic={'vkCmdBeginRendering','vkCmdEndRendering'}
    used=set(re.findall(r'\bp_(vk[A-Z]\w*)\s*\(',nvn+'\n'+draw))
    if not dynamic<=used:raise ValueError('Runtime mudou dynamic rendering, revisar')
    exports=set(re.findall(r'\bVKAPI_CALL\s+(vk[A-Z]\w*)\s*\(',ex))
    if not {'vkCreateInstance','vkCreateDevice'}<=exports:raise ValueError('Parser de exports mudou')
    absent=sorted(dynamic-exports)
    return {'etapa':23,'runtime_vulkan':'.'.join(map(str,req)),
      'backend_header_vulkan':'.'.join(bk.groups()),
      'dynamic_rendering_no_runtime':True,
      'nao_encontrados_em_exports':absent,'exports_identificados':len(exports),
      'backend_opengnm_pronto_sem_mudanca':False if got<req or absent else 'NAO_COMPROVADO',
      'mesa_requires_orbis_compat':'orbis-compat' in f['mesa_build'],
      'mesa_requires_porting_kit':'orbis-porting-kit' in f['mesa_build'],
      'readme_opengnm_diz_vulkan_1_0':bool(re.search(r'Vulkan\s+1\.0',f['readme'])),
      'urls_publicas':[url(k) for k in SOURCES],
      'pkg_gerado':False,'console_testado':False,'codigo_comercial':False,
      'viabilidade_castlevania':'INDETERMINADA',
      'limite':'Ausencia em um unico arquivo de exports nao exclui caminhos alternativos, e versao declarada nao comprova suporte em hardware.'}
def report(x):
    return f'''# Kazuma Etapa 23 — Compatibilidade Vulkan (somente estatica)

**A viabilidade do port completo continua INDETERMINADA.** Nenhum PKG ou teste no PS4.

| Item | Evidencia no codigo publico |
|---|---|
| Runtime pede | Vulkan {x['runtime_vulkan']} |
| Header de vulkan-ps4 declara | Vulkan {x['backend_header_vulkan']} |
| Runtime usa dynamic rendering? | Sim: vkCmdBeginRendering / vkCmdEndRendering |
| Funcoes nao encontradas no arquivo de exports | {', '.join(x['nao_encontrados_em_exports']) or 'Nenhuma'} |
| Mesa PS4 testado com NVN no console? | Nao |

O backend OpenGNM examinado nao e uma substituicao direta comprovada: a versao declarada e inferior, e os dois comandos de dynamic rendering nao aparecem no arquivo de exports. O README menciona Vulkan 1.0, enquanto o header declara {x['backend_header_vulkan']}: nenhum deles prova funcionamento real no console. A alternativa Mesa-PS4 tem dependencias adicionais e nao foi compilada ou executada aqui.

**Proxima prova util:** iniciar um backend Vulkan de verdade no PS4, obter versao/extensoes e testar dynamic rendering, shaders SPIR-V e swapchain antes de tentar NVN. Memoria e loader do jogo continuam pendentes.

## Fontes fixadas
'''+'\n'.join('- '+u for u in x['urls_publicas'])+'\n'
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();x=analyze(fetch());a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'resultado.json').write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (a.out/'RELATORIO.md').write_text(report(x),encoding='utf-8')
    print('ETAPA 23: runtime Vulkan',x['runtime_vulkan'],'backend',x['backend_header_vulkan'])
    print('Dynamic rendering nao encontrado em exports:',x['nao_encontrados_em_exports'])
    print('Console NAO testado; port INDETERMINADO; nenhum PKG.')
if __name__=='__main__':main()
