#!/usr/bin/env python3
"""Nao confundir link parcial com boot real e nao mascarar símbolos não resolvidos."""
from pathlib import Path
import sys, json
TARGETS=['nx::plat::read_pad(', 'nx::plat::vulkan_get_instance_proc_addr()',
         'nx::plat::vulkan_surface_extension()', 'nx::plat::vulkan_create_surface(']
def sym(raw):
    out=set()
    for line in raw.splitlines():
        a=line.strip()
        if a.startswith('U '):out.add(a[2:].strip())
        elif not a or a.startswith(('w ','v ','W ','V ')):continue
        else:raise ValueError('llvm-nm formato inesperado: '+a)
    return out
def analyze(before,after,defs,status):
    removed=[]
    for t in TARGETS:
        found=[s for s in before if s.startswith(t)]
        if len(found)!=1:raise ValueError('Esperado 1 pendencia antes para '+t+': '+repr(found))
        if any(s.startswith(t) for s in after):raise ValueError('Pendente depois: '+t)
        if not any(t in line for line in defs.splitlines()):raise ValueError('Nao definido: '+t)
        removed+=found
    return {'etapa':73,'api_implementadas':len(removed),'simbolos_resolvidos':removed,
     'indefinidos_antes':len(before),'indefinidos_depois':len(after),
     'introduzidos':sorted(after-before),
     'plataforma_pendente':sorted(s for s in after if s.startswith('nx::plat::')),
     'link_estrito':status,'jogo_presente':False,'console_testado':False,
     'pkg_gerado':False,
     'nota':'Vulkan provider depende da vkloader/Mesa REAL, nao incluida neste link estrito OpenOrbis. Compilacao nao comprova executabilidade.'}
def main(path):
 p=Path(path);b=sym((p/'ANTES.nm').read_text());a=sym((p/'DEPOIS.nm').read_text());
 defs='\n'.join((p/x).read_text() for x in ('DEFINIDOS_INPUT.nm','DEFINIDOS_VULKAN.nm'))
 z=analyze(b,a,defs,(p/'LINK_ESTRITO_STATUS.txt').read_text().strip())
 (p/'RELATORIO.json').write_text(json.dumps(z,indent=2,ensure_ascii=False)+'\n')
 (p/'LEIA_PRIMEIRO.txt').write_text('KAZUMA73 / 4 APIs nx::plat / SEM JOGO\n'+\
  f"APIS={z['api_implementadas']}\nINDEFINIDOS_ANTES={z['indefinidos_antes']}\n"+\
  f"INDEFINIDOS_DEPOIS={z['indefinidos_depois']}\nPLAT_PENDENTES={len(z['plataforma_pendente'])}\n"+\
  f"LINK_ESTRITO={z['link_estrito']}\nSEM JOGO, SEM PKG, SEM TESTE PS4.\n")
 print((p/'LEIA_PRIMEIRO.txt').read_text())
if __name__=='__main__':main(sys.argv[1])
