#!/usr/bin/env bash
set -euo pipefail
: "${OO_PS4_TOOLCHAIN:?SDK OpenOrbis ausente}"
: "${RUNNER_TEMP:?somente runner GitHub}"
: "${KAZUMA_NX_SOURCE:?runtime upstream ausente}"
sdk="$OO_PS4_TOOLCHAIN"; out="$RUNNER_TEMP/kazuma39"; rep='relatorios/etapa71'
mkdir -p "$rep"
test -s "$out/kazuma50_boot_partial.o" || { echo 'Falta objeto base da etapa50'; exit 2; }
clang++-18 --target=x86_64-pc-freebsd12-elf -std=c++20 -O1 -fPIC \
    -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE \
    -isysroot "$sdk" -isystem "$sdk/include" -isystem "$sdk/include/c++/v1" \
    -I"$KAZUMA_NX_SOURCE/runtime/src" \
    -c tools/etapa71/platform_ps4_threads.cpp -o "$out/kazuma71_threads.o" \
    > "$rep/COMPILACAO.log" 2>&1 || { cat "$rep/COMPILACAO.log"; exit 3; }
ld.lld-18 -m elf_x86_64 -r \
    -o "$out/kazuma71_boot_partial.o" \
    "$out/kazuma50_boot_partial.o" "$out/kazuma71_threads.o" \
    > "$rep/LINK_PARCIAL.log" 2>&1 || { cat "$rep/LINK_PARCIAL.log"; exit 4; }
llvm-nm-18 -C -u "$out/kazuma50_boot_partial.o" > "$rep/ANTES.nm" || true
llvm-nm-18 -C -u "$out/kazuma71_boot_partial.o" > "$rep/DEPOIS.nm" || true
llvm-nm-18 -C --defined-only "$out/kazuma71_threads.o" > "$rep/DEFINIDOS.nm"
status=FALHOU_LINK_ESTRITO
if ld.lld-18 -m elf_x86_64 -pie --script "$sdk/link.x" \
  --eh-frame-hdr --error-limit=350 -L"$sdk/lib" \
  -o "$out/kazuma71_tentativa.elf" \
  "$sdk/lib/crt1.o" "$out/kazuma71_boot_partial.o" \
  --start-group -lc++ -lc -lkernel -lm --end-group \
  > "$rep/LINK_ESTRITO.log" 2>&1; then
    readelf -W -h "$out/kazuma71_tentativa.elf" > "$rep/ELF_HEADER.txt"
    readelf -W -l "$out/kazuma71_tentativa.elf" > "$rep/ELF_SEGMENTS.txt"
    if grep -Eq 'Machine:.*Advanced Micro Devices X86-64' "$rep/ELF_HEADER.txt" && \
       grep -Eq 'LOAD[[:space:]]' "$rep/ELF_SEGMENTS.txt" && \
       grep -E 'Entry point address:[[:space:]]+0x[0-9a-fA-F]+' "$rep/ELF_HEADER.txt" | grep -Evq '0x0$'; then
       status=PASSOU_ELF_INTERMEDIARIO
    fi
fi
printf '%s\n' "$status" > "$rep/LINK_ESTRITO_STATUS.txt"
python3 tools/etapa71/avaliar.py "$rep"
