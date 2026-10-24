#!/usr/bin/env bash
set -euo pipefail
: "${OO_PS4_TOOLCHAIN:?}"; : "${KAZUMA_NX_SOURCE:?}"; : "${RUNNER_TEMP:?}"
sdk="$OO_PS4_TOOLCHAIN"
out="$RUNNER_TEMP/kazuma39"
rep="relatorios/etapa74"
mkdir -p "$rep"
test -s "$out/kazuma73_runtime_partial.o" || { echo 'A base real da etapa73 está ausente' >&2; exit 2; }
echo '[74/1] Compilar seis funções VideoOut para PS4 OpenOrbis.'
clang++-18 --target=x86_64-pc-freebsd12-elf -std=c++20 -O1 -fPIC \
 -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE \
 -isysroot "$sdk" -isystem "$sdk/include" -isystem "$sdk/include/c++/v1" \
 -I"$sdk/include" -I"$KAZUMA_NX_SOURCE/runtime/src" \
 -c tools/etapa74/platform_ps4_display.cpp -o "$out/kazuma74_videoout.o" > "$rep/COMPILACAO.log" 2>&1 || { cat "$rep/COMPILACAO.log"; exit 3; }
echo '[74/2] Integrar a nx::boot com os seis símbolos (link relocável).'
ld.lld-18 -m elf_x86_64 -r -o "$out/kazuma74_runtime_partial.o" \
 "$out/kazuma73_runtime_partial.o" "$out/kazuma74_videoout.o" \
 > "$rep/LINK_PARCIAL.log" 2>&1 || { cat "$rep/LINK_PARCIAL.log"; exit 4; }
llvm-nm-18 -C -u "$out/kazuma73_runtime_partial.o" > "$rep/ANTES.nm" || true
llvm-nm-18 -C -u "$out/kazuma74_runtime_partial.o" > "$rep/DEPOIS.nm" || true
llvm-nm-18 -C --defined-only "$out/kazuma74_videoout.o" > "$rep/DEFINIDOS.nm"
echo '[74/3] Tentar link estrito, sem suprimir símbolo.'
status=FALHOU_LINK_ESTRITO
if ld.lld-18 -m elf_x86_64 -pie --script "$sdk/link.x" --eh-frame-hdr --error-limit=350 -L"$sdk/lib" \
 -o "$out/kazuma74_tentativa.elf" "$sdk/lib/crt1.o" "$out/kazuma74_runtime_partial.o" \
 --start-group -lc++ -lc -lkernel -lScePad -lSceUserService -lSceVideoOut -lm --end-group > "$rep/LINK_ESTRITO.log" 2>&1; then
    readelf -W -h "$out/kazuma74_tentativa.elf" > "$rep/ELF_HEADER.txt"
    if grep -Eq 'Machine:.*Advanced Micro Devices X86-64' "$rep/ELF_HEADER.txt"; then
        status=PASSOU_ELF_INTERMEDIARIO
    fi
fi
printf '%s\n' "$status" > "$rep/LINK_ESTRITO_STATUS.txt"
echo '[74/4] Auditar símbolos realmente resolvidos.'
python3 tools/etapa74/avaliar.py "$rep"
