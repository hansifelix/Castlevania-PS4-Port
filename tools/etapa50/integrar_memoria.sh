#!/usr/bin/env bash
# Build de 3 APIs de memoria; nunca instala/executa mapeamento no PS4.
set -euo pipefail
: "${OO_PS4_TOOLCHAIN:?falta SDK OpenOrbis}"
: "${RUNNER_TEMP:?somente runner do GitHub Actions}"
: "${KAZUMA_NX_SOURCE:?falta upstream}"
sdk="$OO_PS4_TOOLCHAIN"
out="$RUNNER_TEMP/kazuma39"
rep='relatorios/etapa50'
mkdir -p "$rep"
test -s "$out/kazuma49_boot_partial.o" || { echo 'Falta resultado parcial Etapa49' >&2; exit 2; }

printf '[50/1] Compilar 3 APIs de memoria para o alvo PS4, SEM executar.\n'
clang++-18 --target=x86_64-pc-freebsd12-elf -std=c++20 -O1 -fPIC \
  -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE \
  -isysroot "$sdk" -isystem "$sdk/include" -isystem "$sdk/include/c++/v1" \
  -I"$KAZUMA_NX_SOURCE/runtime/src" \
  -c tools/etapa50/platform_ps4_memory.cpp \
  -o "$out/kazuma50_memory.o" > "$rep/COMPILACAO.log" 2>&1 || {
    cat "$rep/COMPILACAO.log"; echo 'ETAPA50: COMPILACAO_FALHOU' >&2; exit 3;
  }

printf '[50/2] Ligar parcialmente ao BOOT real, sem silenciar erros.\n'
ld.lld-18 -m elf_x86_64 -r -o "$out/kazuma50_boot_partial.o" \
  "$out/kazuma49_boot_partial.o" "$out/kazuma50_memory.o" \
  > "$rep/LINK_PARCIAL.log" 2>&1 || {
    cat "$rep/LINK_PARCIAL.log"; echo 'ETAPA50: LINK_PARCIAL_FALHOU' >&2; exit 4;
  }
llvm-nm-18 -C -u "$out/kazuma49_boot_partial.o" > "$rep/ANTES.nm" || true
llvm-nm-18 -C -u "$out/kazuma50_boot_partial.o" > "$rep/DEPOIS.nm" || true
llvm-nm-18 -C --defined-only "$out/kazuma50_memory.o" > "$rep/DEFINIDOS.nm"

printf '[50/3] Tentar link estrito sem --unresolved nem stubs.\n'
status=FALHOU_LINK_ESTRITO
if ld.lld-18 -m elf_x86_64 -pie --script "$sdk/link.x" \
  --eh-frame-hdr --error-limit=350 -L"$sdk/lib" \
  -o "$out/kazuma50_tentativa.elf" \
  "$sdk/lib/crt1.o" "$out/kazuma50_boot_partial.o" \
  --start-group -lc++ -lc -lkernel -lm --end-group \
  > "$rep/LINK_ESTRITO.log" 2>&1; then
  readelf -W -h "$out/kazuma50_tentativa.elf" > "$rep/ELF_HEADER.txt"
  readelf -W -l "$out/kazuma50_tentativa.elf" > "$rep/ELF_SEGMENTS.txt"
  if grep -Eq 'Machine:.*Advanced Micro Devices X86-64' "$rep/ELF_HEADER.txt" && \
     grep -Eq 'LOAD[[:space:]]' "$rep/ELF_SEGMENTS.txt" && \
     grep -E 'Entry point address:[[:space:]]+0x[0-9a-fA-F]+' "$rep/ELF_HEADER.txt" | grep -Evq '0x0$'; then
    status=PASSOU_ELF_INTERMEDIARIO
  fi
fi
printf '%s\n' "$status" > "$rep/LINK_ESTRITO_STATUS.txt"

printf '[50/4] Gerar relatorio auditavel.\n'
python3 tools/etapa50/avaliar.py "$rep"
test -s "$rep/LEIA_PRIMEIRO.txt" && test -s "$rep/RELATORIO.json"
echo 'Etapa 50: analise de ligacao terminada. Nao ha jogo, nem PKG, nem memoria testada no PS4.'
