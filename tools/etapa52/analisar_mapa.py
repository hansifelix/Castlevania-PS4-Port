#!/usr/bin/env python3
"""Etapa 52: plano estatico auditavel; NUNCA mapeia RAM e NAO acessa dados do jogo."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

PAGE = 16384  # E51 mediu sysconf(_SC_PAGESIZE)=16384; e uma observacao, nao universal
UPSTREAM_COMMIT = '4043f21bb4f656d34cd17ba070238c7728d00631'
# Memoria host no ramo nao-Apple, nao-Android do runtime/include/nx/runtime.h, commit fixado.
HOST = [
    ('heap', 0x5000000000, 0x180000000),
    ('alias', 0x5800000000, 0x1000000000),
    ('stack', 0x6800000000, 0x100000000),
    ('kernel', 0x6A00000000, 0x100000000),
    ('thunk', 0x6F00000000, 0x100000),
]

def round_up(v: int, a: int) -> int:
    if v < 0 or a <= 0 or (a & (a - 1)):
        raise ValueError('tamanho/alinhamento invalido')
    return (v + a - 1) & ~(a - 1)

def mk_range(name: str, start: int, size: int, *, kind: str) -> dict:
    if size <= 0 or start % PAGE or size % PAGE or start + size >= 1 << 64:
        raise ValueError(f'regiao invalida/alinhamento: {name}')
    return dict(nome=name, tipo=kind, inicio=start, fim_exclusivo=start+size,
                inicio_hex=f'0x{start:X}', fim_hex=f'0x{start+size:X}',
                reservado_bytes=size, reservado_mib=round(size/(1024**2), 2),
                reservado_gib=round(size/(1024**3), 3))

def audit(manifest: dict) -> dict:
    if manifest.get('content_version') != '1.1.0':
        raise ValueError('versao do conteudo inesperada: nao misturar atualizacoes')
    ms = manifest.get('modules')
    if not isinstance(ms,list) or len(ms)!=3 or [m.get('name') for m in ms] != ['main','sdk','subsdk0']:
        raise ValueError('lista de modulos inesperada')
    expected = {'main':0x4000000000,'sdk':0x4010000000,'subsdk0':0x4020000000}
    modules=[]
    for m in ms:
        n=m['name'];base=int(m['base'],16);length=m['image_bytes']
        if base != expected[n] or not isinstance(length,int) or length<=0:
            raise ValueError(f'dados do modulo divergentes: {n}')
        if len(m.get('image_sha256',''))!=64 or len(m.get('nso_sha256_reference',''))!=64:
            raise ValueError(f'faltam hashes de referencia do modulo {n}')
        # ATENCAO: image_bytes e apenas um PISO de referencia e nao o intervalo
        # real exigido por ModuleInfo.bss + ModuleInfo.bss_size.
        r=mk_range(n,base,round_up(length,PAGE),kind='modulo_piso_imagem')
        r.update(image_bytes=length, image_sha256_referencia=m['image_sha256'],
                 bss_conhecido=False, mapa_completo=False,
                 alerta='PISO de tamanho, NAO equivale a ModuleInfo.bss+bss_size')
        modules.append(r)
    guest=[mk_range(n,s,l,kind='host_virtual_planejado') for n,s,l in HOST]
    intervals=sorted(modules+guest, key=lambda v:v['inicio'])
    for a,b in zip(intervals,intervals[1:]):
        if a['fim_exclusivo']>b['inicio']:
            raise ValueError('sobreposicao entre faixas publicas: '+a['nome']+' / '+b['nome'])
    for v in intervals:
        if v['inicio'] % PAGE or v['fim_exclusivo'] % PAGE:
            raise ValueError('faixas nao alinhadas')
    min_module_span=modules[-1]['fim_exclusivo']-modules[0]['inicio']
    result={'etapa':52,'status':'AUDITORIA_ESTATICA_SEM_TESTE_PS4',
            'versao_conteudo':manifest['content_version'],
            'bundle_version_mac':manifest.get('bundle_version'),
            'commit_upstream':UPSTREAM_COMMIT,'pagina_observada_etapa51_bytes':PAGE,
            'modulos':modules,'faixas_host':guest,'piso_intervalo_modulos_bytes':min_module_span,
            'piso_intervalo_modulos_mib':round(min_module_span/1048576,2),
            'host_total_virtual_reservado_gib':round(sum(v['reservado_bytes'] for v in guest)/1073741824,3),
            'conflitos_neste_plano_publico':0,
            'provas_exigidas_antes_de_testar_reserva_grande':[
                'Obter metadados AOT reais ModuleInfo.bss e ModuleInfo.bss_size da copia legal compativel, sem publica-los',
                'Revalidar tamanhos reais e posicoes no PS4; imagem publica e apenas piso',
                'Distinguir espaco virtual reservado de RAM fisica comprometida',
                'Verificar se reservas grandes cabem no espaco virtual do processo (nao provado na Etapa 51)',
                'Verificar politica de memoria FreeBSD/OpenOrbis e seguranca sem MAP_FIXED',
                'Revisar liberacao do registro de reservas no adaptador: munmap externo nao limpa slot'
            ],'sem_pkg':True,'sem_nsp':True,'sem_aot_comercial':True}
    return result

def markdown(a:dict)->str:
    ls=['# KAZUMA PORT GAMES BR — Etapa 52: mapa publico de memoria',
        '', '**RESULTADO:** auditoria estatica, NAO um teste de hardware.',
        f"- Referencia Switch: conteudo {a['versao_conteudo']} (upstream fixado `{a['commit_upstream']}`).",
        f"- Pagina observada na Etapa 51: **{a['pagina_observada_etapa51_bytes']:,} bytes** (16 KiB).",
        f"- Piso da faixa dos modulos: **{a['piso_intervalo_modulos_mib']} MiB**, incluindo espacos entre as bases.",
        '- `image_bytes` NAO inclui necessariamente toda a BSS/alocacoes do guest; nao e tamanho real da reserva.',
        '', '| Faixa | Inicio | Fim exclusivo (piso) | Tamanho (MiB) |',
        '|---|---|---|---:|']
    for m in a['modulos']+a['faixas_host']:
        ls.append(f"| {m['nome']} | `{m['inicio_hex']}` | `{m['fim_hex']}` | {m['reservado_mib']} |")
    ls+=['', f"**Espaco virtual nominal das faixas host:** {a['host_total_virtual_reservado_gib']} GiB.",
         'Reservar 64 GiB de enderecos virtuais NAO e o mesmo que consumir 64 GiB de RAM.',
         '', '## Limites das conclusoes',
         '- Etapa 51 demonstrou reserva de UMA pagina em cada base; nao a reserva de modulos inteiros.',
         '- Esta auditoria NAO executa `nx::boot()`, NAO verifica GPUs, threads ou executabilidade.',
         '- Os intervalos host nao mostraram sobreposicao com os PISOS de imagem neste plano publico. Isso nao garante que as faixas estejam livres no PS4.',
         '- Em particular, o runtime nao-Apple/nao-Android pede heap de 6 GiB e alias de 64 GiB de espaco VIRTUAL.',
         '', '## Proximos bloqueios verificaveis']
    ls+=['- '+x for x in a['provas_exigidas_antes_de_testar_reserva_grande']]
    ls+=['', '## Origem publica',
         f"`https://github.com/SwonDev/cstlvnia-blmont-to-macos/tree/{a['commit_upstream']}`",
         '`games/castlevania/build.json` e `runtime/include/nx/runtime.h` (ramo nao-Apple/nao-Android).',
         '', '**NAO subir NSP, ExeFS, RomFS, arquivos AOT derivados do jogo ou copias comerciais no repo publico.**','']
    return '\n'.join(ls)

def verificar_runtime(raw: str) -> None:
    # Esperados do ramo nao-Apple/nao-Android, nao do mapa macOS/Android.
    for name, value in (('kHeapBase',0x5000000000),('kHeapMax',0x180000000),
                        ('kAliasBase',0x5800000000),('kAliasSize',0x1000000000),
                        ('kStackBase',0x6800000000),('kStackSize',0x100000000),
                        ('kKernelBase',0x6A00000000),('kKernelSize',0x100000000),
                        ('kThunkBase',0x6F00000000),('kThunkSize',0x100000)):
        if f'constexpr uint64_t {name} = 0x{value:X}ull;' not in raw and \
           f'constexpr uint64_t {name} = 0x{value:x}ull;' not in raw:
            raise ValueError(f'Constante {name} mudou no upstream: revisar antes de usar!')

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--saida',default='relatorios/etapa52');p.add_argument('--comparar-upstream',default=None);p.add_argument('--comparar-runtime',default=None)
    args=p.parse_args()
    raw=Path(args.manifest).read_bytes();m=json.loads(raw)
    if args.comparar_upstream:
        original=json.loads(Path(args.comparar_upstream).read_text(encoding='utf-8'))
        if original!=m:raise ValueError('Manifesto publico difere do upstream fixado!')
    if args.comparar_runtime:
        verificar_runtime(Path(args.comparar_runtime).read_text(encoding='utf-8'))
    a=audit(m);a['hash_manifest_sha256']=hashlib.sha256(raw).hexdigest()
    out=Path(args.saida);out.mkdir(parents=True,exist_ok=True)
    (out/'MAPA_MEMORIA.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'LEIA_PRIMEIRO.md').write_text(markdown(a),encoding='utf-8')
    print('KAZUMA52: AUDITORIA_ESTATICA_OK / SEM_PKG / SEM_JOGO')
    print('KAZUMA52: PISO_INTERVALO_MODULOS_MIB='+str(a['piso_intervalo_modulos_mib']))
    print('KAZUMA52: VIRTUAL_HOST_GIB='+str(a['host_total_virtual_reservado_gib']))
    print('KAZUMA52: NAO GARANTE RESERVAS REAIS NO PS4')
if __name__=='__main__':main()
