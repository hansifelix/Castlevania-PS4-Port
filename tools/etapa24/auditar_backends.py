#!/usr/bin/env python3
"""Etapa 24: audit only public, pinned source code. NO console access, no game data."""
from __future__ import annotations
import argparse
import json
import re
import urllib.error
import urllib.request
import time
from pathlib import Path

COMMITS = {
    "runtime": ("SwonDev/cstlvnia-blmont-to-macos", "4043f21bb4f656d34cd17ba070238c7728d00631"),
    "opengnm": ("PS4-OpenGNM/vulkan-ps4", "f4d940b723771b3fe637e8ac0704bb5d6ab19622"),
    "mesa": ("orbis-ports/mesa-ps4", "1a59cc147b54e3970814b37313e2f27357672e9d"),
}
SOURCES = {
    "runtime_device": ("runtime", "runtime/src/nvn/nvn_vk.cpp"),
    "runtime_draw": ("runtime", "runtime/src/nvn/nvn_draw.cpp"),
    "gnm_header": ("opengnm", "include/vk_ps4_internal.h"),
    "gnm_exports": ("opengnm", "src/vk_ps4_entrypoints.c"),
    "mesa_radv": ("mesa", "src/amd/vulkan/radv_physical_device.c"),
    "mesa_wsi": ("mesa", "src/vulkan/wsi/wsi_orbis.c"),
    "mesa_readme": ("mesa", "build-support/orbis/README.md"),
    "mesa_build": ("mesa", "build-support/orbis/build.sh"),
    "mesa_entrypoint": ("mesa", "ps4/build.sh"),
}

def url(key: str) -> str:
    label, path = SOURCES[key]
    repo, revision = COMMITS[label]
    return f"https://raw.githubusercontent.com/{repo}/{revision}/{path}"

def fetch_sources() -> dict[str, str]:
    result = {}
    for key in SOURCES:
        request = urllib.request.Request(url(key), headers={"User-Agent":"Kazuma-Etapa24-Public-Audit/1.0"})
        error = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=35) as response:
                    raw = response.read(500001)
                    if len(raw) > 500000:
                        raise ValueError(f"Fonte muito grande: {key}")
                    result[key] = raw.decode("utf-8-sig")
                    break
            except (urllib.error.URLError, TimeoutError) as exc:
                error = exc
                if attempt < 2:
                    time.sleep(2)
        if key not in result:
            raise RuntimeError(f"Nao foi possivel obter {key}: {error}")
    return result

def uncomment(text: str) -> str:
    return re.sub(r"//[^\n]*", "", re.sub(r"/\*.*?\*/", "", text, flags=re.S))

def analyze(src: dict[str,str]) -> dict:
    if set(src) != set(SOURCES):
        raise ValueError("Conjunto incompleto de fontes, auditoria cancelada")
    rt = uncomment(src['runtime_device'])
    draw = uncomment(src['runtime_draw'])
    hdr = uncomment(src['gnm_header'])
    exports = uncomment(src['gnm_exports'])
    mesa = uncomment(src['mesa_radv'])
    wsi = src['mesa_wsi']
    runtime_version = re.search(r'\bapp\.apiVersion\s*=\s*VK_API_VERSION_(\d+)_(\d+)', rt)
    backend_version = re.search(r'#define\s+VK_PS4_API_VERSION\s+VK_MAKE_VERSION\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)',hdr)
    if not runtime_version or not backend_version:
        raise ValueError('Regras de versao diferentes das fixadas; revisar antes de prosseguir')
    runtime_minor = tuple(map(int, runtime_version.groups()))
    gnm_minor = tuple(map(int, backend_version.groups()[:2]))
    if runtime_minor != (1,3):
        raise ValueError(f'Versao do runtime mudou: {runtime_minor}')
    needed = {'vkCmdBeginRendering','vkCmdEndRendering'}
    used = set(re.findall(r'\bp_(vk[A-Z]\w*)\s*\(', rt + '\n' + draw))
    if not needed <= used:
        raise ValueError('Runtime mudou uso de dynamic rendering; revisar')
    available = set(re.findall(r'\bVKAPI_CALL\s+(vk[A-Z]\w*)\s*\(', exports))
    if not {'vkCreateInstance','vkCreateDevice'} <= available:
        raise ValueError('Arquivo de exports mudou formato')
    gfx7_1_3 = bool(re.search(
        r'\.apiVersion\s*=\s*pdev->info\.gfx_level\s*>=\s*GFX8\s*\?\s*RADV_API_VERSION\s*:\s*RADV_API_VERSION_1_3',
        mesa))
    if not gfx7_1_3:
        raise ValueError('RAMO GFX7 DA RADV AUSENTE: nao inferir Vulkan 1.3')
    wsi_videoout = ('#if defined(__PS4__)' in wsi and
                    'sceVideoOutRegisterBuffers' in wsi and
                    'sceVideoOutSubmitFlip' in wsi)
    if not wsi_videoout:
        raise ValueError('WSI Orbis VideoOut nao identificado')
    mesa_build = src['mesa_build'] + '\n' + src['mesa_entrypoint']
    dependencies = [dep for dep in ('orbis-compat','orbis-porting-kit') if dep in mesa_build]
    if len(dependencies) != 2:
        raise ValueError('Dependencias da compilacao Mesa mudaram')
    return {
        'etapa':24,
        'resultado':'MESA_RADV_CANDIDATO_PRIORITARIO_PARA_VALIDACAO',
        'runtime_vulkan':'.'.join(map(str,runtime_minor)),
        'runtime_usa_dynamic_rendering':True,
        'opengnm_header_vulkan':'.'.join(backend_version.groups()),
        'opengnm_dynamic_rendering_ausente_neste_arquivo_de_exports':sorted(needed-available),
        'mesa_radv_gfx7_declara_vulkan_1_3':gfx7_1_3,
        'mesa_wsi_orbis_codigo_videoout_encontrado':wsi_videoout,
        'mesa_requisitos_de_build':dependencies,
        'mesa_readme_alega_driver_compilado_e_link_probes':('libvulkan_radeon.a' in src['mesa_readme'] and 'link probe' in src['mesa_readme']),
        'mesa_no_gitHub_compilada_nesta_etapa':False,
        'mesa_testada_no_PS4_do_usuario':False,
        'opengnm_testado_no_PS4_do_usuario':False,
        'castlevania_testado':False,
        'port_completo_viavel':'INDETERMINADO',
        'proxima_validacao':'compilar backend Mesa com dependencias fixadas; testar inicializacao, GPU properties, extensoes, shaders e apresentacao no console com homebrew minimo antes do runtime',
        'avisos':[
            'Codigo-fonte nao e prova de execucao real na GPU do PS4.',
            'Versao Vulkan 1.3 declarada para GFX7 nao assegura extensoes e formatos completos.',
            'Ausencia em arquivo de exports do OpenGNM nao prova ausencia em todo o projeto.',
            'O runtime e o codigo do jogo ainda precisam de loader, memoria e servicos.'
        ],
        'fontes_publicas_fixadas':[url(k) for k in SOURCES],
        'sem_pkg':True,
        'sem_dados_comerciais':True,
    }

def report(x:dict) -> str:
    absent=', '.join(x['opengnm_dynamic_rendering_ausente_neste_arquivo_de_exports']) or 'nenhuma neste arquivo'
    return f"""# Kazuma Port Games BR — Etapa 24: escolha provisoria de backend grafico

**Resultado:** {x['resultado']}. **Viabilidade do port: {x['port_completo_viavel']}**.

| Verificacao | Evidencia estatica | Limite |
|---|---|---|
| Runtime | Pede Vulkan **{x['runtime_vulkan']}**, usa dynamic rendering | Nao foi testado no PS4 |
| Vulkan sobre OpenGNM | Header declara **{x['opengnm_header_vulkan']}** | Versao inferior; requer adaptacao |
| Comandos nao identificados no arquivo de exports OpenGNM | `{absent}` | Ausencia somente no arquivo examinado |
| Mesa RADV para GPU GFX7 | Codigo tem ramo de **Vulkan 1.3** | Nao prova implementacao de extensoes nem execucao no console |
| Mesa WSI Orbis | Trechos VideoOut incluidos no fonte | Nao foi feito teste de apresentacao no console |
| Build Mesa | Depende de `{', '.join(x['mesa_requisitos_de_build'])}` | Build novo nao foi executado nesta etapa |
| README Mesa | Alega driver compilado e link probe | Declaracao do repositorio, nao verificacao independente nesta etapa |

## Decisao provisoria

**Priorizar Mesa RADV/orbis-ports na proxima validacao**, porque o codigo examinado contem caminho GFX7/Vulkan 1.3 e WSI para VideoOut. Isso e uma *hipotese de integracao*, nao autorizacao para instalar um PKG.

O backend OpenGNM permanece como alternativa, mas **na revisao analisada** nao e substituto direto do contrato Vulkan 1.3 do runtime. Uma camada de compatibilidade precisaria oferecer ou reescrever os comandos faltantes.

## Proxima prova realmente util

1. Reproduzir o build da RADV PS4 com `orbis-compat` e `orbis-porting-kit`, em ambiente isolado. Testar link de uma aplicacao minima, registrar hash e simbolos.
2. Apenas se o build for confiavel, criar um teste de hardware que relate versao Vulkan, propriedades do dispositivo, extensoes, shaders e apresentacao.
3. Integrar backend ao runtime **somente depois**; em paralelo, continua pendente a memoria, o carregador, os modulos e os servicos do jogo.

**Nenhum codigo comercial, arquivo de jogo ou PKG foi utilizado ou criado; o PS4 nao foi ligado.**

## Fontes auditadas (revisoes imutaveis)

"""+ '\n'.join('- '+v for v in x['fontes_publicas_fixadas']) + '\n'

def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();result=analyze(fetch_sources());args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (args.out/'RELATORIO.md').write_text(report(result),encoding='utf-8')
    print('ETAPA 24: Mesa RADV GFX7 declara Vulkan 1.3 e WSI Orbis presente no codigo; nao testados no PS4.')
    print('OpenGNM revisao fixada:',result['opengnm_header_vulkan'],'dynamic rendering nao encontrado nos exports indicados.')
    print('DECISAO PROVISORIA: investigar Mesa RADV. Nenhum PKG. Port segue INDETERMINADO.')
if __name__ == '__main__':main()
