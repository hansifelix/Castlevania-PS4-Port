#!/usr/bin/env bash
# Kazuma Etapa 41: integra 87 objetos com 3 + 5 APIs da plataforma PS4.
# Executado SOMENTE no GitHub Actions. Não contém o jogo e não gera PKG.
set -euo pipefail

: "${KAZUMA_NX_SOURCE:?Fonte do runtime nao configurada pela Etapa 39}"
: "${OO_PS4_TOOLCHAIN:?OpenOrbis nao configurado pela Etapa 39}"
: "${RUNNER_TEMP:?Ambiente do GitHub Actions nao detectado}"

out="$RUNNER_TEMP/kazuma39"
report="relatorios/etapa41"
mkdir -p "$report"
test -s "$out/runtime_com_plataforma_partial.o"
test -s tools/etapa40/platform_ps4_files.cpp

echo '[41/1] Compilando cinco APIs de arquivo para x86-64 PS4.'
clang++-18 --target=x86_64-pc-freebsd12-elf -std=c++20 -O1 -fPIC \
  -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE \
  -isysroot "$OO_PS4_TOOLCHAIN" \
  -isystem "$OO_PS4_TOOLCHAIN/include" \
  -isystem "$OO_PS4_TOOLCHAIN/include/c++/v1" \
  -I"$KAZUMA_NX_SOURCE/runtime/src" \
  -c tools/etapa40/platform_ps4_files.cpp \
  -o "$out/platform_ps4_files.o" 2>&1 | tee "$report/COMPILACAO_CINCO_APIS.txt"

echo '[41/2] Link relocavel: 87 objetos + 3 APIs + 5 APIs.'
ld.lld-18 -m elf_x86_64 -r \
  -o "$out/runtime_etapa41_partial.o" \
  "$out/runtime_com_plataforma_partial.o" \
  "$out/platform_ps4_files.o" 2>&1 | tee "$report/LINK_PARCIAL.txt"

readelf -h "$out/runtime_etapa41_partial.o" > "$report/ELF.txt"
grep -Eq 'Machine:.*Advanced Micro Devices X86-64' "$report/ELF.txt"
llvm-nm-18 -C -u "$out/runtime_com_plataforma_partial.o" | LC_ALL=C sort -u > "$report/INDEFINIDOS_ANTES.txt" || true
llvm-nm-18 -C -u "$out/runtime_etapa41_partial.o" | LC_ALL=C sort -u > "$report/INDEFINIDOS_DEPOIS.txt" || true
llvm-nm-18 -C --defined-only "$out/runtime_etapa41_partial.o" > "$report/DEFINIDOS.txt"
llvm-nm-18 -C --defined-only "$out/platform_ps4_files.o" > "$report/DEFINIDOS_CINCO_APIS.txt"
llvm-nm-18 -C -u "$out/platform_ps4_files.o" > "$report/DEPENDENCIAS_NOVAS_APIS.txt" || true

python3 tools/etapa41/relatorio_simbolos.py "$report"
sha256sum "$out/runtime_etapa41_partial.o" > "$report/SHA256.txt"
echo 'Etapa 41: relatorio de integracao gerado. Objeto relocavel NAO e executavel ou PKG.'
