#!/usr/bin/env bash
# Executado no GitHub runner Linux, nao no celular ou PS4.
set -euo pipefail
[[ $# == 3 ]] || { echo 'Uso: <sdk> <nx-src> <recompiler-src>' >&2; exit 2; }
sdk="$(cd "$1" && pwd)"; nx="$(cd "$2" && pwd)"; recomp_src="$(cd "$3" && pwd)"
for f in "$sdk/link.x" "$sdk/lib/crt1.o" "$nx/runtime/include/nx/cpu.h" "$recomp_src/recomp/emit.py"; do
  test -s "$f" || { echo "Ausente: $f" >&2; exit 2; }
done
out="$(pwd)/relatorios/etapa21"; mkdir -p "$out"
scratch="$(mktemp -d)"; trap 'rm -rf "$scratch"' EXIT
# Ambiente Python isolado; o codigo comercial nao e baixado nem acessado.
python3 -m venv "$scratch/venv"
"$scratch/venv/bin/pip" -q install --disable-pip-version-check 'capstone==5.0.6' 'lz4==4.4.4'
export PYTHONPATH="$recomp_src"
printf '[1/5] Desmontando ARM64 sintético e gerando C++ pelo recompiler upstream...\n'
"$scratch/venv/bin/python" tools/etapa21/gerar_recomp_sintetico.py --out "$scratch/gen" \
  >"$out/gerar.stdout.txt" 2>"$out/gerar.stderr.txt" || {
    cat "$out/gerar.stderr.txt" >&2; exit 1;
  }
cp "$scratch/gen/geracao.json" "$out/geracao.json"
cp "$scratch/gen/code.cpp" "$out/codigo_gerado_sintetico.cpp"
printf '[2/5] Executando C++ gerado em Linux x86-64 (teste sem PS4)...\n'
c++ -std=c++20 -O1 -I"$nx/runtime/include" -I"$scratch/gen" \
  "$scratch/gen/main.cpp" "$scratch/gen/code.cpp" -o "$scratch/host_test" \
  >"$out/host_build.stdout.txt" 2>"$out/host_build.stderr.txt" || { cat "$out/host_build.stderr.txt" >&2; exit 1; }
"$scratch/host_test" || { echo 'ERRO: resultado do programa recompilado difere de 43' >&2; exit 1; }
# OpenOrbis libc++ v0.5.4 nao implementa todos os recursos de C++20.
# Adapta somente nx/cpu.h no runner, preservando a fonte original.
mkdir -p "$scratch/compat/nx"
cat > "$scratch/compat/nx/kazuma_cpu_compat.h" <<'CPP_COMPAT'
#pragma once
#include <cstdlib>
#include <cstdint>
#include <type_traits>
namespace kazuma_cpu_compat {
template <typename To, typename From>
constexpr To bit_cast(const From& from) noexcept {
    static_assert(sizeof(To) == sizeof(From), "bit_cast: tamanhos diferentes");
    static_assert(std::is_trivially_copyable_v<To> && std::is_trivially_copyable_v<From>,
                  "bit_cast: tipos nao triviais");
    return __builtin_bit_cast(To, from);
}
template <typename T>
constexpr T rotr(T value, int shift) noexcept {
    static_assert(std::is_unsigned_v<T>, "rotr: requer tipo sem sinal");
    constexpr int bits=int(sizeof(T)*8);
    int n=((shift % bits) + bits) % bits;
    return n ? T((value >> n) | (value << (bits-n))) : value;
}
}
CPP_COMPAT
python3 - "$nx/runtime/include/nx/cpu.h" "$scratch/compat/nx/cpu.h" <<'PY_COMPAT'
from pathlib import Path
import sys
orig=Path(sys.argv[1]).read_text(encoding='utf-8')
assert orig.count('#include <bit>')==1
assert orig.count('std::bit_cast')>=5
assert orig.count('std::rotr(')==2
patched=(orig.replace('#include <bit>', '#include "kazuma_cpu_compat.h"')
             .replace('std::bit_cast','kazuma_cpu_compat::bit_cast')
             .replace('std::rotr(','kazuma_cpu_compat::rotr('))
Path(sys.argv[2]).write_text(patched,encoding='utf-8')
PY_COMPAT
printf '[3/5] Compilando C++ GERADO para PS4 x86-64 (OpenOrbis)...\n'
flags=(--target=x86_64-pc-freebsd12-elf -std=c++20 -O1 -fPIC -funwind-tables \
       -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE \
       -isysroot "$sdk" -isystem "$sdk/include" -isystem "$sdk/include/c++/v1" \
       -I"$scratch/compat" -I"$nx/runtime/include" -I"$scratch/gen")
clang++ "${flags[@]}" -c "$scratch/gen/code.cpp" -o "$scratch/code.o" \
  >"$out/compilar_codigo.stdout.txt" 2>"$out/compilar_codigo.stderr.txt" || { cat "$out/compilar_codigo.stderr.txt" >&2; exit 1; }
clang++ "${flags[@]}" -c "$scratch/gen/main.cpp" -o "$scratch/main.o" \
  >"$out/compilar_main.stdout.txt" 2>"$out/compilar_main.stderr.txt" || { cat "$out/compilar_main.stderr.txt" >&2; exit 1; }
printf '[4/5] Ligando ELF de alvo PS4, sem converter em eboot nem PKG...\n'
ld.lld -m elf_x86_64 -pie --script "$sdk/link.x" --eh-frame-hdr \
  -L"$sdk/lib" -o "$scratch/test.elf" "$sdk/lib/crt1.o" \
  "$scratch/code.o" "$scratch/main.o" -lc -lkernel -lc++ \
  >"$out/link.stdout.txt" 2>"$out/link.stderr.txt" || { cat "$out/link.stderr.txt" >&2; exit 1; }
readelf -h "$scratch/test.elf" >"$out/elf_header.txt"
readelf -Ws "$scratch/test.elf" >"$out/elf_symbols.txt"
printf '[5/5] Registrando provas e limitacoes...\n'
python3 - "$scratch/test.elf" "$out" <<'PY_REPORT'
import json,sys,hashlib
from pathlib import Path
elf=Path(sys.argv[1]);out=Path(sys.argv[2]);h=(out/'elf_header.txt').read_text()
assert 'ELF64' in h and 'X86-64' in h
r=json.loads((out/'geracao.json').read_text(encoding='utf-8'))
r.update({'compilou_recompilado_cpp_no_ps4':True,
          'linkou_elf_target_ps4':True,
          'executou_cpp_gerado_em_linux':True,
          'executou_elf_no_ps4':False,
          'gerou_pkg':False,
          'sha256_elf':hashlib.sha256(elf.read_bytes()).hexdigest(),
          'viabilidade_castlevania':'INDETERMINADA',
          'bloqueios':['memoria guest fixa','modulos reais','NVN/shaders','servicos do sistema','codigo do jogo']})
(out/'resultado.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('ETAPA 21: recompiler publico gerou C++, Linux executou 43, PS4 ELF ligado OFFLINE; nenhum PKG.')
PY_REPORT
