#!/usr/bin/env bash
# Etapa 48: integra adaptador PS4 de temporizacao real e tenta ligar BOOT do runtime.
# SEM GAME, SEM PKG, SEM stubs, SEM ignorar simbolos indefinidos.
set -euo pipefail
: "${OO_PS4_TOOLCHAIN:?SDK OpenOrbis nao configurado}"
: "${KAZUMA_NX_SOURCE:?Runtime publico upstream nao configurado}"
: "${RUNNER_TEMP:?Somente ambiente GitHub Actions}"
repo="${GITHUB_WORKSPACE:-$PWD}"
cd "$repo"
sdk="$OO_PS4_TOOLCHAIN"
src="$KAZUMA_NX_SOURCE"
out="$RUNNER_TEMP/kazuma39"
rep="relatorios/etapa48"
mkdir -p "$rep" "$out"
test -s "$out/runtime_etapa41_partial.o" || { echo 'ERRO: faltou runtime parcial da Etapa 41' >&2; exit 2; }
test -s "$src/runtime/src/main.cpp" || { echo 'ERRO: upstream runtime/src/main.cpp ausente' >&2; exit 2; }
test -s "$sdk/lib/crt1.o" && test -s "$sdk/link.x" || { echo 'ERRO: SDK incompleto' >&2; exit 2; }
flags=(--target=x86_64-pc-freebsd12-elf -std=c++20 -O0 -fPIC -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE
  -isysroot "$sdk" -isystem "$sdk/include" -isystem "$sdk/include/c++/v1"
  -I"$RUNNER_TEMP/compat" -I"$src/runtime/include" -I"$src/runtime/src" -I"$src/runtime/src/nvn" )
if [[ -n "${KAZUMA_VK_HEADERS:-}" ]]; then flags+=("-I$KAZUMA_VK_HEADERS"); fi

# O jogo NAO pode rodar sem seus módulos recompilados; mesmo uma compilacao
# bem-sucedida de main.cpp apenas valida a ponte do runtime.
echo '[48/1] Compilando o nx::boot() REAL do runtime publico, nao um mock.'
if ! clang++-18 "${flags[@]}" -c "$src/runtime/src/main.cpp" -o "$out/nx_boot_real.o" >"$rep/COMPILAR_BOOT.log" 2>&1; then
  echo 'Falhou a compilacao do nx::boot; consulte COMPILAR_BOOT.log.'
  python3 tools/etapa48/relatorio.py "$rep" --compile FALHOU --partial NAO_TENTADO --strict NAO_TENTADO
  exit 0
fi
if ! clang++-18 "${flags[@]}" -c tools/etapa48/entry_ps4.cpp -o "$out/entry_ps4.o" >>"$rep/COMPILAR_BOOT.log" 2>&1; then
  echo 'Falhou o ponto de entrada PS4; consulte COMPILAR_BOOT.log.'
  python3 tools/etapa48/relatorio.py "$rep" --compile FALHOU --partial NAO_TENTADO --strict NAO_TENTADO
  exit 0
fi

echo '[48/2] Link relocavel: 87 objetos do runtime + 8 APIs + nx::boot e main do PS4.'
if ! ld.lld-18 -m elf_x86_64 -r -o "$out/kazuma48_boot_partial.o" \
    "$out/runtime_etapa41_partial.o" "$out/nx_boot_real.o" "$out/entry_ps4.o" \
    >"$rep/LINK_PARCIAL_BOOT.log" 2>&1; then
  python3 tools/etapa48/relatorio.py "$rep" --compile PASSOU --partial FALHOU --strict NAO_TENTADO
  exit 0
fi
llvm-nm-18 -C -u "$out/kazuma48_boot_partial.o" | LC_ALL=C sort -u > "$rep/SIMBOLOS_PENDENTES_BOOT.txt" || true
llvm-nm-18 -C --defined-only "$out/kazuma48_boot_partial.o" | grep -E 'nx::boot\(| main$' > "$rep/DEFINIDOS_BOOT.txt" || true

echo '[48/3] LINK ESTRITO de nx::boot, sem game modules e sem ignorar falhas.'
status=FALHOU
if ld.lld-18 -m elf_x86_64 -pie --script "$sdk/link.x" \
    --eh-frame-hdr --error-limit=350 -L"$sdk/lib" \
    -o "$out/kazuma48_boot_tentativa.elf" "$sdk/lib/crt1.o" "$out/kazuma48_boot_partial.o" \
    --start-group -lc++ -lc -lkernel -lm --end-group \
    >"$rep/LINK_ESTRITO_BOOT.log" 2>&1; then
  # Somente contar como ELF quando ha LOAD e entrada diferentes de zero.
  readelf -W -h "$out/kazuma48_boot_tentativa.elf" > "$rep/ELF_HEADER.txt"
  readelf -W -l "$out/kazuma48_boot_tentativa.elf" > "$rep/ELF_SEGMENTS.txt"
  if grep -Eq 'Machine:.*Advanced Micro Devices X86-64' "$rep/ELF_HEADER.txt" && \
     grep -Eq 'LOAD[[:space:]]' "$rep/ELF_SEGMENTS.txt" && \
     grep -E 'Entry point address:[[:space:]]+0x[0-9a-fA-F]+' "$rep/ELF_HEADER.txt" | grep -Evq '0x0$'; then
    status=PASSOU_ELF_INTERMEDIARIO
  fi
fi

echo '[48/4] Relatorio de bloqueios prioritarios (sem game comercial).'
python3 tools/etapa48/relatorio.py "$rep" --compile PASSOU --partial PASSOU --strict "$status"
cat "$rep/LEIA_PRIMEIRO.txt"
test -s "$rep/RESUMO.json"
# 0: analise concluida (mesmo que link estrito falhe). A status real consta no JSON.
