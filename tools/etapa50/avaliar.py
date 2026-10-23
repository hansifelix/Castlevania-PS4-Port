#!/usr/bin/env python3
"""Auditoria sem mascarar link estrito; verde nao significa runtime funcional."""
import json
from pathlib import Path
import sys
TARGETS=('nx::plat::reserve(', 'nx::plat::commit(', 'nx::plat::decommit(')

def symbols(path):
    values=set()
    for row in Path(path).read_text(encoding='utf-8').splitlines():
        row=row.strip()
        if row.startswith('U '): values.add(row[2:].strip())
        elif row.startswith(('w ','W ')): pass
        elif row: raise ValueError('llvm-nm -u inesperado: '+row)
    return values

def analyze(before,after,defined,status):
    for x in TARGETS:
        b=[y for y in before if y.startswith(x)]
        if len(b)!=1: raise ValueError('Esperado exatamente um simbolo PENDENTE: '+x+' '+repr(b))
        if any(y.startswith(x) for y in after): raise ValueError('Ainda indefinido: '+x)
        if x not in defined: raise ValueError('Objeto nao definiu: '+x)
    removed=sorted(before-after)
    added=sorted(after-before)
    platform=sorted(y for y in after if y.startswith('nx::plat::'))
    return {'etapa':50,'apis_memoria_resolvidas':len(TARGETS),
      'indefinidos_antes':len(before),'indefinidos_depois':len(after),
      'resolvidos':len(removed),'novas_dependencias':len(added),
      'nomes_resolvidos':removed,'novos_simbolos':added,
      'plataforma_pendente':len(platform),'simbolos_plataforma_pendentes':platform,
      'link_estrito':status,'elf_intermediario':status=='PASSOU_ELF_INTERMEDIARIO',
      'memoria_ps4_testada_no_hardware':False,
      'jogo_presente':False,'pkg_gerado':False,
      'cuidados':['Nao usar MAP_FIXED: mmap com hint + conferir endereco exato',
                  'sysconf(_SC_PAGESIZE) em vez de assumir paginas de 4096 bytes',
                  'Somente modificar regioes reservadas por este adaptador',
                  'madvise nao comprova liberacao fisica de paginas',
                  'Teste local Linux nao prova suporte a enderecos do jogo no PS4']}

def report(path):
    p=Path(path)
    b=symbols(p/'ANTES.nm');a=symbols(p/'DEPOIS.nm')
    d=(p/'DEFINIDOS.nm').read_text(encoding='utf8')
    status=(p/'LINK_ESTRITO_STATUS.txt').read_text().strip()
    data=analyze(b,a,d,status)
    (p/'RELATORIO.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    (p/'PENDENTES_PLATAFORMA.txt').write_text('\n'.join(data['simbolos_plataforma_pendentes'])+'\n',encoding='utf8')
    (p/'LEIA_PRIMEIRO.txt').write_text(
        'KAZUMA PORT GAMES BR / ETAPA 50 - MEMORIA DO RUNTIME\n'
        '=================================================\n'
        f"MEMORIA_APIS_RESOLVIDAS={data['apis_memoria_resolvidas']}\n"
        f"SIMBOLOS_ANTES={data['indefinidos_antes']}\n"
        f"SIMBOLOS_DEPOIS={data['indefinidos_depois']}\n"
        f"SIMBOLOS_RESOLVIDOS_TOTAL={data['resolvidos']}\n"
        f"NOVAS_DEPENDENCIAS={data['novas_dependencias']}\n"
        f"PLATAFORMA_PENDENTE={data['plataforma_pendente']}\n"
        f"LINK_ESTRITO={status}\n"
        'SEM PKG, SEM JOGO, SEM EXECUCAO DE MEMORIA NO PS4.\n'
        'PRIORIDADE: verificar comportamento real do mapeamento na plataforma em teste ISOLADO.\n',encoding='utf8')
    print((p/'LEIA_PRIMEIRO.txt').read_text())

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('Uso: avaliar.py relatorios/etapa50')
    report(sys.argv[1])
