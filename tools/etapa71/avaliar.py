#!/usr/bin/env python3
"""Relatório de símbolos reais: CI verde NÃO significa executável ou jogo."""
import json
import sys
from pathlib import Path

TARGETS = ('nx::plat::start_thread(', 'nx::plat::exit_thread()', 'nx::plat::yield()')

def nm_undefined(raw):
    values=set()
    for line in raw.splitlines():
        row=line.strip()
        if row.startswith('U '):
            values.add(row[2:])
        elif row.startswith(('w ', 'v ')):
            # Referencias fracas opcionais.
            continue
        elif row:
            raise ValueError('Formato inesperado llvm-nm -u: ' + row)
    return values

def analyze(before, after, definitions, strict):
    for prefix in TARGETS:
        matches=[v for v in before if v.startswith(prefix)]
        if len(matches)!=1:
            raise ValueError(f'Esperava um único símbolo do runtime para {prefix}: {matches}')
        if any(v.startswith(prefix) for v in after):
            raise ValueError('Ainda indefinido após integração: '+prefix)
        if not any(prefix in d for d in definitions.splitlines()):
            raise ValueError('Implementação não definida no objeto: '+prefix)
    game=sorted(v for v in after if
                v in ('nx_module_main','nx_module_sdk') or v.startswith('nx::game::')
                or 'nx::linked_modules(' in v)
    plat=sorted(v for v in after if v.startswith('nx::plat::'))
    return dict(etapa=71, apis_thread_definidas=len(TARGETS),
                indefinidos_antes=len(before),indefinidos_depois=len(after),
                removidos=sorted(before-after), introduzidos=sorted(after-before),
                plataforma_pendente=plat, modulos_jogo_pendentes=game,
                link_estrito=strict, elf_intermediario=(strict=='PASSOU_ELF_INTERMEDIARIO'),
                homebrew_testado_ps4=False, jogo_executado=False, pkg=False)

def main(path):
    p=Path(path)
    b=nm_undefined((p/'ANTES.nm').read_text())
    a=nm_undefined((p/'DEPOIS.nm').read_text())
    r=analyze(b,a,(p/'DEFINIDOS.nm').read_text(),(p/'LINK_ESTRITO_STATUS.txt').read_text().strip())
    (p/'RELATORIO.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
    resumo=(f"KAZUMA71: Threads POSIX PS4 — integração do runtime público\n"
            f"APIS_RESOLVIDAS={r['apis_thread_definidas']}\n"
            f"INDEFINIDOS_ANTES={r['indefinidos_antes']}\n"
            f"INDEFINIDOS_DEPOIS={r['indefinidos_depois']}\n"
            f"PLATAFORMA_PENDENTE={len(r['plataforma_pendente'])}\n"
            f"SIMBOLOS_JOGO_AUSENTES={len(r['modulos_jogo_pendentes'])}\n"
            f"LINK_ESTRITO={r['link_estrito']}\n"
            'Aviso: LINK -r é parcial, sem módulos AOT, sem PKG e sem jogo.\n')
    (p/'LEIA_PRIMEIRO.txt').write_text(resumo)
    print(resumo)
if __name__ == '__main__':
    if len(sys.argv)!=2: raise SystemExit('uso: avaliar.py relatorios/etapa71')
    main(sys.argv[1])
