#!/usr/bin/env bash
# Ligacao real dos objetos do runtime da Etapa 48 com novas implementacoes.
# Check verde indica auditoria completada, sem esconder falhas de link final.
set -euo pipefail
: "${OO_PS4_TOOLCHAIN:?falta OpenOrbis}"
: "${KAZUMA_NX_SOURCE:?falta runtime publico}"
: "${RUNNER_TEMP:?somente runner do GitHub}"
sdk="$OO_PS4_TOOLCHAIN"
src="$KAZUMA_NX_SOURCE"
out="$RUNNER_TEMP/kazuma39"
rep="relatorios/etapa49"
mkdir -p "$rep"
test -s "$out/kazuma48_boot_partial.o" || { echo 'Falta objeto da Etapa 48' >&2; exit 2; }

echo '[49/1] Compilar seis funcoes concretas de host com OpenOrbis.'
clang++-18 --target=x86_64-pc-freebsd12-elf -std=c++20 -O1 -fPIC \
    -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE \
    -isysroot "$sdk" -isystem "$sdk/include" -isystem "$sdk/include/c++/v1" \
    -I"$src/runtime/src" \
    -c tools/etapa49/platform_ps4_host_basics.cpp \
    -o "$out/kazuma49_host_basics.o" > "$rep/COMPILACAO.log" 2>&1 || {
    cat "$rep/COMPILACAO.log"
    echo 'ERRO de compilacao da Etapa 49. Check VERMELHO.' >&2; exit 3;
}

echo '[49/2] Link -r: runtime real + boot + 6 APIs basicas de host.'
ld.lld-18 -m elf_x86_64 -r \
    -o "$out/kazuma49_boot_partial.o" \
    "$out/kazuma48_boot_partial.o" "$out/kazuma49_host_basics.o" \
    > "$rep/LINK_PARCIAL.log" 2>&1 || {
    cat "$rep/LINK_PARCIAL.log"
    echo 'Link parcial falhou. Check VERMELHO.' >&2; exit 4;
}
llvm-nm-18 -C -u "$out/kazuma48_boot_partial.o" > "$rep/ANTES.nm" || true
llvm-nm-18 -C -u "$out/kazuma49_boot_partial.o" > "$rep/DEPOIS.nm" || true
llvm-nm-18 -C --defined-only "$out/kazuma49_host_basics.o" > "$rep/DEFINIDOS_ADAPTADOR.nm"

echo '[49/3] Tentar link final ESTRITO; falha de dependencia sera registrada.'
status=FALHOU_LINK_ESTRITO
if ld.lld-18 -m elf_x86_64 -pie --script "$sdk/link.x" \
    --eh-frame-hdr --error-limit=350 -L"$sdk/lib" \
    -o "$out/kazuma49_elf_tentativa.elf" \
    "$sdk/lib/crt1.o" "$out/kazuma49_boot_partial.o" \
    --start-group -lc++ -lc -lkernel -lm --end-group \
    > "$rep/LINK_ESTRITO.log" 2>&1; then
    readelf -W -h "$out/kazuma49_elf_tentativa.elf" > "$rep/ELF_HEADER.txt"
    readelf -W -l "$out/kazuma49_elf_tentativa.elf" > "$rep/ELF_SEGMENTS.txt"
    if grep -Eq 'Machine:.*Advanced Micro Devices X86-64' "$rep/ELF_HEADER.txt" && \
       grep -Eq 'LOAD[[:space:]]' "$rep/ELF_SEGMENTS.txt" && \
       grep -E 'Entry point address:[[:space:]]+0x[0-9a-fA-F]+' "$rep/ELF_HEADER.txt" | grep -Evq '0x0$'; then
       status=PASSOU_ELF_INTERMEDIARIO
    fi
fi
printf '%s\n' "$status" > "$rep/STATUS_LINK_ESTRITO.txt"

echo '[49/4] Validar seis APIs e publicar contador honesto.'
python3 tools/etapa49/avaliar.py "$rep"
test -s "$rep/LEIA_PRIMEIRO.txt"
test -s "$rep/RELATORIO.json"
echo 'Nota: Mesmo que o link final venha a passar, BOOT COM JOGO NAO FOI TESTADO.'
