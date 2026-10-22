#!/usr/bin/env python3
"""Auditoria ESTATICA das APIs públicas nx::plat versus a ponte experimental PS4.
Nenhum mapeamento, compilação comercial, carga de jogo ou teste no console.
"""
import argparse
import json
import re
from pathlib import Path

UPSTREAM = '4043f21bb4f656d34cd17ba070238c7728d00631'
# Conjunto priorizado e explícito: não é contagem de todas as APIs do runtime.
CATEGORIAS = {
    'memoria_guest_fixa': ['reserve', 'commit', 'decommit'],
    'threads_tempo': ['start_thread', 'exit_thread', 'exit_process', 'sleep_ns', 'yield', 'current_thread_id', 'monotonic_ns'],
    'arquivos': ['fopen_utf8', 'ftell64', 'fseek64', 'read_at', 'make_dirs'],
    'sistema': ['log_line', 'data_root', 'setting'],
    'janela_video': ['create_window', 'release_window', 'window_generation', 'window_minimized', 'window_size', 'desktop_size', 'screen_size', 'default_render_scale'],
    'controle': ['read_pad'],
    'audio': ['audio_open', 'audio_submit', 'audio_queued', 'audio_pause'],
    'vulkan': ['vulkan_get_instance_proc_addr', 'vulkan_surface_extension', 'vulkan_create_surface'],
}


def strip_comments(s):
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    return re.sub(r'//[^\n]*', '', s)


def declared(text, name):
    """Assinatura simples da declaracao; nao considera funcao inline nem comentários."""
    text = strip_comments(text)
    return bool(re.search(r'\b' + re.escape(name) + r'\s*\([^;{}]*\)\s*;', text))


def defined(text, name):
    """Definicao C++ simples e explícita no arquivo PS4, não chamada à função."""
    text = strip_comments(text)
    pat = (r'(?m)^\s*(?:(?:FILE\s*\*|[A-Za-z_][\w:<>,*&]*)\s+)+'
           + re.escape(name) + r'\s*\([^;{}]*\)\s*\{')
    return bool(re.search(pat, text))


def audit(header, ps4):
    detailed=[]
    categories={}
    for category, names in CATEGORIAS.items():
        rows=[]
        for name in names:
            exists=declared(header,name)
            if not exists:
                raise ValueError('Contrato não encontrado no upstream: ' + name)
            impl=defined(ps4,name)
            row={'nome':name, 'declarado_upstream':True, 'definicao_encontrada_na_ponte_ps4':impl,
                 'testado_em_execucao_real_ps4_nesta_etapa':False}
            rows.append(row)
            detailed.append({'categoria':category,**row})
        categories[category]={'total_amostrado':len(rows), 'definicoes_encontradas':sum(x['definicao_encontrada_na_ponte_ps4'] for x in rows), 'funcoes':rows}
    found=sum(x['definicao_encontrada_na_ponte_ps4'] for x in detailed)
    return {
        'etapa':19, 'modelo':'auditoria de código-fonte; a presença de definição não comprova equivalência funcional',
        'fonte_upstream_commit':UPSTREAM,
        'total_interfaces_priorizadas':len(detailed),
        'definicoes_ps4_encontradas':found,
        'ainda_sem_definicao_ps4':len(detailed)-found,
        'grupos':categories,
        'gates_para_port':{
            'espaco_enderecamento_guest_fixo_compatível_ps4':'NAO_COMPROVADO',
            'recompilacao_AArch64_para_x86_64_do_jogo':'NAO_IMPLEMENTADA_NO_PS4',
            'carregamento_modulos_originais':'NAO_COMPROVADO',
            'traducao_NVN_para_api_grafica_adequada_ao_PS4':'NAO_IMPLEMENTADA',
            'menu_original_rodando_no_PS4':'NAO',
        },
        'go_no_go':'SEM_DECISAO_DE_VIABILIDADE',
        'aviso':'NÃO executar reservas grandes/fixas, não instalar PKG; sem arquivos do jogo.'
    }


def render(result):
    lines=['# Kazuma — Etapa 19: lacunas de plataforma e portas de viabilidade','',
      'Auditoria **estática** do cabeçalho público `nx::plat` e de `tools/etapa17/plat_ps4.cpp`. Nenhum APK, NSP ou jogo usado.','',
      f"**Interfaces priorizadas:** {result['total_interfaces_priorizadas']}; com definição textual: {result['definicoes_ps4_encontradas']}; sem definição textual: {result['ainda_sem_definicao_ps4']}.",
      '', '**Definição textual não é prova de compatibilidade**, desempenho nem sucesso no PS4.','',
      '| Grupo | Definições na ponte PS4 | Total verificado |','|---|---:|---:|']
    for name,g in result['grupos'].items():
        lines.append(f"| {name} | {g['definicoes_encontradas']} | {g['total_amostrado']} |")
    lines+=['','## Interfaces ainda não implementadas (amostra priorizada)']
    for name,g in result['grupos'].items():
        missing=[f['nome'] for f in g['funcoes'] if not f['definicao_encontrada_na_ponte_ps4']]
        if missing: lines.append('- **'+name+'**: '+', '.join('`'+x+'`' for x in missing))
    lines+=['','## Decisões para o projeto','',
      '1. **Bloqueio memória**: conferir mapa real do processo PS4 e modelo guest; não usar MAP_FIXED indiscriminadamente.',
      '2. **Bloqueio código**: estabelecer caminho executável AArch64 recompilado → x86-64, ligação e carregamento de módulos; ainda não demonstrado.',
      '3. **Bloqueio gráficos**: encontrar estratégia concreta para NVN/shaders no PS4; o homebrew gráfico atual não testa isso.',
      '4. **Bloqueio conteúdo**: um teste sem jogo não executa nem valida o menu original.',
      '', '**Conclusão:** não é possível dar SIM ou NÃO definitivo ao port com esses testes; existem impedimentos ainda não resolvidos.',
      'Não criar PKG, não tocar no PS4 nem publicar recursos comerciais nesta etapa.','']
    return '\n'.join(lines)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--header',required=True,type=Path)
    ap.add_argument('--ps4',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    result=audit(args.header.read_text(encoding='utf-8'),args.ps4.read_text(encoding='utf-8'))
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'lacunas.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (args.out/'DIAGNOSTICO.md').write_text(render(result),encoding='utf-8')
    print(f"ETAPA 19: {result['definicoes_ps4_encontradas']}/{result['total_interfaces_priorizadas']} interfaces com definição textual; análise ESTÁTICA; nenhum PKG.")

if __name__=='__main__':
    main()
