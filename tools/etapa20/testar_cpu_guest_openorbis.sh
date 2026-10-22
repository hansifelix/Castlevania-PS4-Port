#!/usr/bin/env bash
# Apenas cross-compila um microteste de ABI do runtime publico — sem PKG.
set -euo pipefail
if [ "$#" -ne 2 ]; then echo 'Uso: script <diretorio-sdk> <diretorio-fonte-nx>' >&2; exit 2; fi
sdk="$(cd "$1" && pwd)"
nx="$(cd "$2" && pwd)"
for f in "$sdk/link.x" "$sdk/lib/crt1.o" "$nx/runtime/include/nx/cpu.h"; do
    test -s "$f" || { echo "Arquivo obrigatorio ausente: $f" >&2; exit 2; }
done
for cmd in clang++ ld.lld readelf sha256sum python3; do
    command -v "$cmd" >/dev/null 2>&1 || { echo "Ferramenta ausente: $cmd" >&2; exit 2; }
done
out="$(pwd)/relatorios/etapa20"
mkdir -p "$out"
# Isolar os binarios intermediarios: o repositorio recebe somente diagnosticos.
scratch="$(mktemp -d)"; trap 'rm -rf "$scratch"' EXIT
printf '[1/4] Cross-compilando contrato nx::CPU com OpenOrbis para x86_64 PS4...\n'
clang++ --target=x86_64-pc-freebsd12-elf -std=c++20 -O1 -fPIC -funwind-tables \
    -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE \
    -isysroot "$sdk" -isystem "$sdk/include" -isystem "$sdk/include/c++/v1" \
    -I"$nx/runtime/include" \
    -c tools/etapa20/cpu_probe.cpp -o "$scratch/probe.o" \
    >"$out/compilar.stdout.txt" 2>"$out/compilar.stderr.txt" || {
        cat "$out/compilar.stderr.txt" >&2; exit 1;
    }
printf '[2/4] Tentando ligar ELF para target PS4 (nenhuma instalacao)...\n'
ld.lld -m elf_x86_64 -pie --script "$sdk/link.x" --eh-frame-hdr \
    -L"$sdk/lib" -o "$scratch/probe.elf" \
    "$sdk/lib/crt1.o" "$scratch/probe.o" -lc -lkernel -lc++ \
    >"$out/link.stdout.txt" 2>"$out/link.stderr.txt" || {
        cat "$out/link.stderr.txt" >&2; exit 1;
    }
printf '[3/4] Conferindo arquitetura ELF e simbolos...\n'
readelf -h "$scratch/probe.elf" >"$out/elf_header.txt"
readelf -Ws "$scratch/probe.elf" >"$out/elf_symbols.txt"
# Contem o codigo do microteste. Nao foi convertido para eboot nem executado no console.
python3 - "$scratch/probe.o" "$scratch/probe.elf" "$out" <<'PY'
import hashlib, json, pathlib, sys
obj, elf, dest = [pathlib.Path(v) for v in sys.argv[1:]]
header=(dest/'elf_header.txt').read_text()
assert 'ELF64' in header and 'X86-64' in header, 'ELF nao e x86-64'
assert obj.stat().st_size > 100 and elf.stat().st_size > 100
result={
 'etapa':20,
 'alvo':'PS4 x86-64 / OpenOrbis',
 'header_upstream':'nx/cpu.h',
 'codigo_comercial':False,
 'codigo_arm64_recompilado_do_jogo':False,
 'sintetico_estilo_guest':True,
 'compilou_abi_cpu':True,
 'linkou_elf_ps4':True,
 'executado_no_ps4':False,
 'gerou_eboot':False,
 'gerou_pkg':False,
 'viabilidade_menu_original':'NAO_DETERMINADA',
 'sha256_obj':hashlib.sha256(obj.read_bytes()).hexdigest(),
 'sha256_elf':hashlib.sha256(elf.read_bytes()).hexdigest(),
 'obstaculos':['mapa guest fixo nao provado no PS4','codigo do jogo nao compilado','loader nao integrado','NVN/shaders sem backend PS4'],
}
(dest/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('ETAPA 20: nx::CPU compilado e ELF ligado OFFLINE; codigo sintetico; nenhum teste PS4.')
PY
printf '[4/4] Relatorio: relatorios/etapa20/resultado.json — sem PKG.\n'
