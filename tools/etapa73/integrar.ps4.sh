#!/usr/bin/env bash
# Runner real OpenOrbis para 4 contratos: 3 Vulkan, 1 controle.
set -euo pipefail
: "${OO_PS4_TOOLCHAIN:?}"; : "${KAZUMA_NX_SOURCE:?}"; : "${KAZUMA_VK_HEADERS:?}"; : "${RUNNER_TEMP:?}"
sdk="$OO_PS4_TOOLCHAIN"; out="$RUNNER_TEMP/kazuma39"; rep="relatorios/etapa73"
mkdir -p "$rep"
test -s "$out/kazuma72_boot_partial.o" || { echo 'Base 72 ausente'; exit 2; }
flags=(--target=x86_64-pc-freebsd12-elf -std=c++20 -O1 -fPIC
 -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE
 -isysroot "$sdk" -isystem "$sdk/include" -isystem "$sdk/include/c++/v1"
 -I"$sdk/include" -I"$KAZUMA_NX_SOURCE/runtime/src" -I"$KAZUMA_VK_HEADERS" -Itools/etapa73)
clang++-18 "${flags[@]}" -c tools/etapa73/platform_ps4_input.cpp -o "$out/kazuma73_pad.o" > "$rep/COMPILACAO.log" 2>&1 || { cat "$rep/COMPILACAO.log"; exit 3; }
clang++-18 "${flags[@]}" -c tools/etapa62/ps4_vulkan_bridge.cpp -o "$out/kazuma73_nx_vulkan.o" >> "$rep/COMPILACAO.log" 2>&1 || { cat "$rep/COMPILACAO.log"; exit 4; }
clang++-18 "${flags[@]}" -c tools/etapa73/platform_ps4_vulkan_provider.cpp -o "$out/kazuma73_vulkan_provider.o" >> "$rep/COMPILACAO.log" 2>&1 || { cat "$rep/COMPILACAO.log"; exit 5; }
ld.lld-18 -m elf_x86_64 -r -o "$out/kazuma73_runtime_partial.o" \
 "$out/kazuma72_boot_partial.o" "$out/kazuma73_pad.o" "$out/kazuma73_nx_vulkan.o" "$out/kazuma73_vulkan_provider.o" \
 > "$rep/LINK_PARCIAL.log" 2>&1 || { cat "$rep/LINK_PARCIAL.log"; exit 6; }
llvm-nm-18 -C -u "$out/kazuma72_boot_partial.o" > "$rep/ANTES.nm" || true
llvm-nm-18 -C -u "$out/kazuma73_runtime_partial.o" > "$rep/DEPOIS.nm" || true
llvm-nm-18 -C --defined-only "$out/kazuma73_pad.o" > "$rep/DEFINIDOS_INPUT.nm"
llvm-nm-18 -C --defined-only "$out/kazuma73_nx_vulkan.o" > "$rep/DEFINIDOS_VULKAN.nm"
llvm-nm-18 -C --defined-only "$out/kazuma73_vulkan_provider.o" > "$rep/DEFINIDOS_PROVIDER.nm"
status=FALHOU_LINK_ESTRITO
if ld.lld-18 -m elf_x86_64 -pie --script "$sdk/link.x" --eh-frame-hdr --error-limit=350 -L"$sdk/lib" \
 -o "$out/kazuma73_tentativa.elf" "$sdk/lib/crt1.o" "$out/kazuma73_runtime_partial.o" \
 --start-group -lc++ -lc -lkernel -lScePad -lSceUserService -lm --end-group > "$rep/LINK_ESTRITO.log" 2>&1; then
  if readelf -W -h "$out/kazuma73_tentativa.elf" | grep -Eq 'Machine:.*Advanced Micro Devices X86-64'; then
    status=PASSOU_ELF_INTERMEDIARIO
  fi
fi
printf '%s\n' "$status" > "$rep/LINK_ESTRITO_STATUS.txt"
python3 tools/etapa73/avaliar.py "$rep"
