#!/usr/bin/env bash
set -euo pipefail
: "${OO_PS4_TOOLCHAIN:?SDK OpenOrbis não configurado}"
: "${RUNNER_TEMP:?somente GitHub Actions}"
: "${KAZUMA_NX_SOURCE:?runtime não clonado}"
sdk="$OO_PS4_TOOLCHAIN"
out="$RUNNER_TEMP/kazuma39"
report="relatorios/etapa75"
mkdir -p "$report"
test -s "$out/kazuma74_runtime_partial.o" || { echo 'Falta o objeto da Etapa 74' >&2; exit 2; }
echo '[75/1] Compilando backend sinc. AudioOut via SDK PS4'
clang++-18 --target=x86_64-pc-freebsd12-elf -std=c++20 -O1 -fPIC \
 -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE \
 -isysroot "$sdk" -isystem "$sdk/include" -isystem "$sdk/include/c++/v1" \
 -I"$sdk/include" -I"$KAZUMA_NX_SOURCE/runtime/src" \
 -c tools/etapa75/platform_ps4_audio.cpp -o "$out/kazuma75_audio.o" > "$report/COMPILACAO.log" 2>&1 || { cat "$report/COMPILACAO.log"; exit 3; }
echo '[75/2] Link parcial REAL - 87+ objetos, sem arquivos comerciais'
ld.lld-18 -m elf_x86_64 -r -o "$out/kazuma75_runtime_partial.o" \
 "$out/kazuma74_runtime_partial.o" "$out/kazuma75_audio.o" > "$report/LINK_PARCIAL.log" 2>&1 || { cat "$report/LINK_PARCIAL.log"; exit 4; }
llvm-nm-18 -C -u "$out/kazuma74_runtime_partial.o" > "$report/ANTES.nm" || true
llvm-nm-18 -C -u "$out/kazuma75_runtime_partial.o" > "$report/DEPOIS.nm" || true
llvm-nm-18 -C --defined-only "$out/kazuma75_audio.o" > "$report/DEFINIDOS.nm"
llvm-nm-18 -C -u "$out/kazuma75_audio.o" > "$report/IMPORTS_AUDIO.nm" || true
echo '[75/3] Link estrito SEM ignore-unresolved (falha auditável)'
status=FALHOU_LINK_ESTRITO
if ld.lld-18 -m elf_x86_64 -pie --script "$sdk/link.x" --eh-frame-hdr --error-limit=350 -L"$sdk/lib" \
 -o "$out/kazuma75_tentativa.elf" "$sdk/lib/crt1.o" "$out/kazuma75_runtime_partial.o" \
 --start-group -lc++ -lc -lkernel -lSceAudioOut -lScePad -lSceUserService -lSceVideoOut -lm --end-group \
 > "$report/LINK_ESTRITO.log" 2>&1; then
  readelf -W -h "$out/kazuma75_tentativa.elf" > "$report/ELF_HEADER.txt"
  if grep -Eq 'Machine:.*Advanced Micro Devices X86-64' "$report/ELF_HEADER.txt"; then
    status=PASSOU_ELF_INTERMEDIARIO
  fi
fi
printf '%s\n' "$status" > "$report/LINK_ESTRITO_STATUS.txt"
echo '[75/4] Relatório transparente das dependências'
python3 tools/etapa75/avaliar.py "$report"
