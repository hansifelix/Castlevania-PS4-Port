#!/usr/bin/env python3
"""Auditoria honesta do backend de threads nativo PS4 (sem jogo, sem pkg)."""
from pathlib import Path
import json
import sys

TARGETS = (
 'nx::plat::start_thread(',
 'nx::plat::exit_thread()',
 'nx::plat::yield()',
 'nx::plat::current_thread_id()',
 'nx::plat::set_thread_name(',
)
IMPORTS = ('scePthreadCreate', 'scePthreadDetach', 'scePthreadExit',
           'scePthreadYield', 'scePthreadGetthreadid', 'scePthreadRename',
           'scePthreadSelf', 'scePthreadAttrInit',
           'scePthreadAttrSetstacksize', 'scePthreadAttrDestroy')


def undefined_nm(raw):
    values=set()
    weak=set()
    for rawline in raw.splitlines():
        row=rawline.strip()
        if not row: continue
        if row.startswith('U '): values.add(row[2:].strip())
        elif row.startswith(('w ', 'v ', 'W ', 'V ')):
            weak.add(row[2:].strip())
        else: raise ValueError('Formato llvm-nm inesperado: '+row)
    return values, weak


def audit(before, after, definitions, imports, strict):
    removed=set()
    for prefix in TARGETS:
        hits=[symbol for symbol in before if symbol.startswith(prefix)]
        if len(hits)!=1: raise ValueError('Esperava 1 referência antes: '+prefix+' / '+str(hits))
        if any(s.startswith(prefix) for s in after): raise ValueError('Ainda indefinido: '+prefix)
        if not any(prefix in s for s in definitions.splitlines()):
            raise ValueError('Não definido no objeto nativo: '+prefix)
        removed.update(hits)
    if any(p in imp for imp in imports for p in ('pthread_create', 'pthread_exit', 'pthread_detach', 'sched_yield')):
        raise ValueError('O backend PS4 ainda importa pthread POSIX; precisa scePthread')
    absent=[imp for imp in IMPORTS if imp not in imports]
    if absent: raise ValueError('APIs scePthread ausentes do objeto nativo: '+', '.join(absent))
    plat=sorted(s for s in after if s.startswith('nx::plat::'))
    modules=sorted(s for s in after if s.startswith('nx::game::') or s in ('nx_module_main','nx_module_sdk') or 'nx::linked_modules(' in s)
    return {
        'etapa':72,'api_implementadas':len(TARGETS),
        'antes':len(before),'depois':len(after),
        'resolvidas':sorted(removed),'outras_removidas':sorted(before-after-removed),
        'novas_dependencias':sorted(after-before),
        'imports_sce_pthread':list(IMPORTS),'plataforma_pendente':plat,
        'modulos_do_jogo_pendentes':modules,
        'link_estrito':strict,'elf_intermediario':strict=='PASSOU_ELF_INTERMEDIARIO',
        'testou_no_ps4_real':False,'executou_jogo':False,'gerou_pkg':False,
        'observacao':'API PS4 compilada+ligada parcialmente (link -r). Link final, jogo e hardware não validados.'}


def main(path):
    p=Path(path)
    before,_=undefined_nm((p/'ANTES.nm').read_text())
    after,_=undefined_nm((p/'DEPOIS.nm').read_text())
    imports,_=undefined_nm((p/'IMPORTS_NATIVOS.nm').read_text())
    definitions=(p/'DEFINIDOS.nm').read_text()
    strict=(p/'LINK_ESTRITO_STATUS.txt').read_text().strip()
    data=audit(before,after,definitions,imports,strict)
    (p/'RELATORIO.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    summary=(
        'KAZUMA 72 — BACKEND scePthread (SEM JOGO)\n'
        f'APIS_PS4_RESOLVIDAS={data["api_implementadas"]}\n'
        f'INDEFINIDOS_ANTES={data["antes"]}\n'
        f'INDEFINIDOS_DEPOIS={data["depois"]}\n'
        f'PLATAFORMA_PENDENTE={len(data["plataforma_pendente"])}\n'
        f'JOGO_AUSENTE={len(data["modulos_do_jogo_pendentes"])}\n'
        f'LINK_ESTRITO={strict}\n'
        'OBS: Link parcial e imports não são teste no console; falta AOT do jogo.\n')
    (p/'LEIA_PRIMEIRO.txt').write_text(summary)
    print(summary)

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('Uso: avaliar.py DIRETORIO_RELATORIOS')
    main(Path(sys.argv[1]))
