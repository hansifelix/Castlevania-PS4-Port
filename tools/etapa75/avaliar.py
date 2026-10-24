#!/usr/bin/env python3
"""Valida redução real dos símbolos nx::plat; nunca confunde link -r com jogo."""
from pathlib import Path
import sys,json
TARGETS=('nx::plat::audio_open(', 'nx::plat::audio_submit(', 'nx::plat::audio_queued()')
NEEDED=('sceAudioOutInit','sceAudioOutOpen','sceAudioOutOutput')
def nm(raw):
    u=set(); weak=set()
    for line in raw.splitlines():
        row=line.strip()
        if not row: continue
        if row.startswith('U '): u.add(row[2:])
        elif row.startswith(('w ','v ','W ','V ')): weak.add(row[2:])
        else: raise ValueError('Formato llvm-nm inesperado: '+row)
    return u,weak

def analyze(before, after, defined, imports, strict):
    resolved=[]
    for p in TARGETS:
        hit=[x for x in before if x.startswith(p)]
        if len(hit)!=1 or any(x.startswith(p) for x in after):
            raise ValueError('Referência original não removida com exatidão: '+p+' '+repr(hit))
        if not any(p in line for line in defined.splitlines()):
            raise ValueError('Implementação ausente do objeto: '+p)
        resolved+=hit
    for name in NEEDED:
        if name not in imports: raise ValueError('Importação PS4 esperada não encontrada: '+name)
    return {'etapa':75,'apis_audio_resolvidas':3,'resolvidas':resolved,
            'indefinidos_antes':len(before),'indefinidos_depois':len(after),
            'novas_dependencias':sorted(after-before),
            'nx_plat_pendente':sorted(x for x in after if x.startswith('nx::plat::')),
            'link_estrito':strict,'backend_bloqueante':True,
            'ps4_hardware_testado':False,'jogo_presente':False,'pkg_gerado':False}
def main(folder):
    p=Path(folder)
    b,_=nm((p/'ANTES.nm').read_text())
    a,_=nm((p/'DEPOIS.nm').read_text())
    i,_=nm((p/'IMPORTS_AUDIO.nm').read_text())
    z=analyze(b,a,(p/'DEFINIDOS.nm').read_text(),i,(p/'LINK_ESTRITO_STATUS.txt').read_text().strip())
    (p/'RELATORIO.json').write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n')
    summary=('KAZUMA 75 - 3 contratos de audio (SÍNCRONO)\n'
      f'APIS_AUDIO_RESOLVIDAS={z["apis_audio_resolvidas"]}\n'
      f'INDEFINIDOS_ANTES={z["indefinidos_antes"]}\n'
      f'INDEFINIDOS_DEPOIS={z["indefinidos_depois"]}\n'
      f'NX_PLAT_PENDENTES={len(z["nx_plat_pendente"])}\n'
      f'LINK_ESTRITO={z["link_estrito"]}\n'
      'AVISO: Backend bloqueante ainda não validado em hardware; nenhum módulo AOT do jogo presente.\n')
    (p/'LEIA_PRIMEIRO.txt').write_text(summary)
    print(summary)
if __name__=='__main__': main(sys.argv[1])
