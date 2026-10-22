#!/usr/bin/env python3
"""Deriva builder do homebrew ja testado na Etapa 13, sem alterar esse builder."""
from pathlib import Path
import sys


def one(text, old, new):
    n=text.count(old)
    if n!=1:raise RuntimeError(f'Esperava 1 ocorrencia do marcador, houve {n}: {old[:95]}')
    return text.replace(old,new)


def derive(text):
    # Base reproduzivel das ferramentas e estrutura de pkg dos testes anteriores.
    text=one(text,"-I\"$samples/samples/_common\")", "-I\"$samples/samples/_common\" -I\"$KAZUMA_SRC46\")")
    anchor="printf '[2/6] Ligando ELF minimo C++ (grafico CPU / SceVideoOut)...\\n'"
    compile_more="""printf '[1b/6] Compilando as oito APIs REAIS nx::plat...\\n'
clang++ "${flags[@]}" -c tools/etapa38/platform_ps4_core.cpp -o "$scratch/core.o" \\
  >"$out/core.stdout.txt" 2>"$out/core.stderr.txt" || { cat "$out/core.stderr.txt" >&2; exit 1; }
clang++ "${flags[@]}" -c tools/etapa40/platform_ps4_files.cpp -o "$scratch/files.o" \\
  >"$out/files.stdout.txt" 2>"$out/files.stderr.txt" || { cat "$out/files.stderr.txt" >&2; exit 1; }
""" + anchor
    text=one(text,anchor,compile_more)
    text=one(text,'"$sdk/lib/crt1.o" "$scratch/main.o" "$scratch/graphics.o" \\',
        '"$sdk/lib/crt1.o" "$scratch/main.o" "$scratch/graphics.o" "$scratch/core.o" "$scratch/files.o" \\')
    text=one(text,'cp tools/etapa12/assets/icon0.png "$scratch/pkgroot/sce_sys/icon0.png"',
       'cp tools/etapa12/assets/icon0.png "$scratch/pkgroot/sce_sys/icon0.png"\ncp tools/etapa46/fixture/kazuma46.dat "$scratch/pkgroot/kazuma46.dat"')
    text=one(text,'pkg_files=(eboot.bin sce_sys/param.sfo sce_sys/icon0.png sce_sys/about/right.sprx)',
       'pkg_files=(eboot.bin kazuma46.dat sce_sys/param.sfo sce_sys/icon0.png sce_sys/about/right.sprx)')
    text=one(text,"TITLE_ID='BREW91235'", "TITLE_ID='BREW94608'")
    text=one(text,"CONTENT_ID='IV0000-BREW91235_00-KAZUMAPADTEST000'", "CONTENT_ID='IV0000-BREW94608_00-KAZUMA46PERF0000'")
    text=one(text,"TITLE='Kazuma Port Games BR - Test 02'", "TITLE='Kazuma Port Games BR - Benchmark 2D'")
    text=one(text,"VERSION='1.01'", "VERSION='1.00'")
    # Esteja claro nos relatorios que nao e o jogo.
    text=one(text,"'etapa':13", "'etapa':46")
    text=text.replace('etapa13','etapa46').replace('ETAPA13','ETAPA46')
    return text

if __name__=='__main__':
    source=Path('tools/etapa13/compilar_homebrew_pkg.sh')
    if not source.is_file(): raise SystemExit('Etapa13 nao encontrada em main')
    content=derive(source.read_text(encoding='utf-8'))
    out=Path(sys.argv[1] if len(sys.argv)>1 else 'tools/etapa46/compilar_pkg_gerado.sh')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(content,encoding='utf-8')
    print('Builder Etapa46 derivado da Etapa13:',out)
