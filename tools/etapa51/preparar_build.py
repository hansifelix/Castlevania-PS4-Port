#!/usr/bin/env python3
"""Deriva builder testado da Etapa13. Etapa51 usa de verdade a memoria da Etapa50."""
from pathlib import Path
import sys

def one(s,a,b):
    n=s.count(a)
    if n != 1: raise RuntimeError(f'Esperada 1 ocorrencia do marcador, achadas {n}: {a[:100]}')
    return s.replace(a,b,1)

def derive(s):
    s=one(s,'-I"$samples/samples/_common")','-I"$samples/samples/_common" -I"$KAZUMA_SRC47")')
    anchor="printf '[2/6] Ligando ELF minimo C++ (grafico CPU / SceVideoOut)...\\n'"
    extra="""printf '[1b/6] Compilando adaptador REAL de memoria Etapa50...\\n'
clang++ "${flags[@]}" -c tools/etapa50/platform_ps4_memory.cpp -o "$scratch/memory.o" \\
  >"$out/memory.stdout.txt" 2>"$out/memory.stderr.txt" || { cat "$out/memory.stderr.txt" >&2; exit 1; }
"""+anchor
    s=one(s,anchor,extra)
    s=one(s,'"$sdk/lib/crt1.o" "$scratch/main.o" "$scratch/graphics.o" \\',
      '"$sdk/lib/crt1.o" "$scratch/main.o" "$scratch/graphics.o" "$scratch/memory.o" \\')
    s=one(s,"TITLE_ID='BREW91235'", "TITLE_ID='BREW95108'")
    s=one(s,"CONTENT_ID='IV0000-BREW91235_00-KAZUMAPADTEST000'",
      "CONTENT_ID='IV0000-BREW95108_00-KAZUMA51MEM00000'")
    s=one(s,"TITLE='Kazuma Port Games BR - Test 02'",
      "TITLE='Kazuma Port Games BR - Memoria 51'")
    s=one(s,"VERSION='1.01'", "VERSION='1.00'")
    s=one(s,"'etapa':13", "'etapa':51")
    s=s.replace('etapa13','etapa51').replace('ETAPA13','ETAPA51')
    return s

if __name__=='__main__':
    p=Path('tools/etapa13/compilar_homebrew_pkg.sh')
    if not p.is_file():raise SystemExit('Etapa13 ausente na branch main')
    out=Path(sys.argv[1] if len(sys.argv)>1 else 'tools/etapa51/compilar_pkg_gerado.sh')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(derive(p.read_text(encoding='utf-8')),encoding='utf-8')
    print('Builder criado:',out)
