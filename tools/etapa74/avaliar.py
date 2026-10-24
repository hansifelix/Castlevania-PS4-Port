#!/usr/bin/env python3
"""Audit real undefined/defined symbols. Green CI != playable game."""
import json
import sys
from pathlib import Path

TARGETS=(
    'nx::plat::create_window()',
    'nx::plat::release_window(void*)',
    'nx::plat::screen_size(unsigned int&, unsigned int&)',
    'nx::plat::window_generation()',
    'nx::plat::window_minimized()',
    'nx::plat::window_size(unsigned int&, unsigned int&)',
)

def undefined(raw):
    result=set()
    for l in raw.splitlines():
        row=l.strip()
        if not row: continue
        if row.startswith('U '): result.add(row[2:].strip())
        elif row.startswith(('w ','v ','W ','V ')): continue
        else: raise ValueError('Unexpected llvm-nm line: '+row)
    return result

def analyze(before, after, defined, status):
    for target in TARGETS:
        assert target in before, f'Missing expected runtime reference before: {target}'
        assert target not in after, f'Still unresolved: {target}'
        assert any(target in s for s in defined.splitlines()), f'Not compiled: {target}'
    others=sorted(s for s in after if s.startswith('nx::plat::'))
    return {
        'etapa':74,
        'apis_videoout_implementadas':len(TARGETS),
        'resolvidas':sorted(TARGETS),
        'simbolos_indefinidos_antes':len(before),
        'simbolos_indefinidos_depois':len(after),
        'novas_dependencias':sorted(after-before),
        'plataforma_pendente':others,
        'modulos_jogo_ausentes':sorted(s for s in after if s.startswith('nx::game::') or s in ('nx_module_main','nx_module_sdk') or 'nx::linked_modules(' in s),
        'link_estrito':status,
        'ps4_hardware_testado':False,
        'game_testado':False,
        'pkg_gerado':False,
        'nota':'VideoOut query uses transient handle; Mesa WSI concurrent use and suspend/resume NOT tested. Guest AOT and RomFS not present.'}

def main(directory):
    p=Path(directory)
    out=analyze(undefined((p/'ANTES.nm').read_text()), undefined((p/'DEPOIS.nm').read_text()),
       (p/'DEFINIDOS.nm').read_text(), (p/'LINK_ESTRITO_STATUS.txt').read_text().strip())
    (p/'RELATORIO.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    text='\n'.join([
        'KAZUMA74 / VideoOut display PS4 / SEM JOGO',
        f'APIS_DISPLAY={out["apis_videoout_implementadas"]}',
        f'INDEFINIDOS_ANTES={out["simbolos_indefinidos_antes"]}',
        f'INDEFINIDOS_DEPOIS={out["simbolos_indefinidos_depois"]}',
        f'NX_PLAT_RESTANTES={len(out["plataforma_pendente"])}',
        'NX_PLAT_NOMES='+', '.join(out['plataforma_pendente']),
        'LINK_ESTRITO='+out['link_estrito'],
        'NÃO COMPROVA EXECUÇÃO NO PS4, NEM PKG, NEM O JOGO.',''])
    (p/'LEIA_PRIMEIRO.txt').write_text(text)
    print(text)

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: avaliar.py relatorios/etapa74')
    main(sys.argv[1])
