#!/usr/bin/env bash
# 8 APIs reais com entry proprio + link estrito; resultados guardados SEM executaveis.
set -euo pipefail
: "${OO_PS4_TOOLCHAIN:?SDK OpenOrbis ausente}"
: "${KAZUMA_SRC44:?Header publico platform.h ausente}"
: "${RUNNER_TEMP:?Apenas GitHub Actions}"
rep='relatorios/etapa44'
mkdir -p "$rep" "$RUNNER_TEMP/kazuma44"
sdk="$OO_PS4_TOOLCHAIN"
out="$RUNNER_TEMP/kazuma44"
for f in "$sdk/link.x" "$sdk/lib/crt1.o" "$sdk/lib/libc.a" "$KAZUMA_SRC44/platform.h"; do
  test -s "$f" || { echo "ARQUIVO_AUSENTE=$f" | tee -a "$rep/FALHA_ENV.txt"; exit 2; }
done
if [[ ! -s "$sdk/lib/libkernel.so" && ! -s "$sdk/lib/libkernel.a" ]]; then
 echo 'ARQUIVO_AUSENTE=libkernel' | tee -a "$rep/FALHA_ENV.txt"; exit 2
fi
flags=(--target=x86_64-pc-freebsd12-elf -std=c++20 -O1 -fPIC
 -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE
 -isysroot "$sdk" -isystem "$sdk/include" -isystem "$sdk/include/c++/v1"
 -I"$KAZUMA_SRC44")
: > "$rep/COMPILACAO.log"
for stem in core files smoke; do
 case "$stem" in
  core) src=tools/etapa38/platform_ps4_core.cpp;;
  files) src=tools/etapa40/platform_ps4_files.cpp;;
  smoke) src=tools/etapa44/smoke_real.cpp;;
 esac
 if ! clang++-18 "${flags[@]}" -c "$src" -o "$out/$stem.o" >> "$rep/COMPILACAO.log" 2>&1; then
   echo "FALHA_COMPILACAO=$src" | tee "$rep/STATUS.txt"
   tail -n 40 "$rep/COMPILACAO.log"
   exit 1
 fi
done
# Confirma que os oito simbolos das duas unidades realmente existem.
llvm-nm-18 -C --defined-only "$out/core.o" "$out/files.o" > "$rep/APIS_DEFINIDAS.txt"
python3 - "$rep/APIS_DEFINIDAS.txt" <<'PY_CHECK'
from pathlib import Path
import sys
x=Path(sys.argv[1]).read_text()
names=('log_line(', 'monotonic_ns(', 'sleep_ns(', 'fopen_utf8(', 'ftell64(', 'fseek64(', 'read_at(', 'make_dirs(')
for n in names:
 if 'nx::plat::'+n not in x:raise SystemExit(f'API x86-64 nao encontrada: {n}')
print('OITO_APIS_PRESENTES=SIM')
PY_CHECK
printf '[44] Realizando link estrito sem ignorar referencias indefinidas...\n'
libs=(-lc++ -lc -lkernel)
[[ -s "$sdk/lib/libm.a" || -s "$sdk/lib/libm.so" ]] && libs+=(-lm)
printf '%s\n' "${libs[@]}" > "$rep/LIBS.txt"
status=FALHOU_LINK_ESTRITO
if ld.lld-18 -m elf_x86_64 -pie --script "$sdk/link.x" --eh-frame-hdr \
 -L"$sdk/lib" -o "$out/smoke_8apis.elf" \
 "$sdk/lib/crt1.o" "$out/smoke.o" "$out/core.o" "$out/files.o" \
 --start-group "${libs[@]}" --end-group > "$rep/LINK.log" 2>&1; then
 readelf -h "$out/smoke_8apis.elf" > "$rep/HEADER_ELF.txt"
 readelf -W -l "$out/smoke_8apis.elf" > "$rep/SEGMENTOS_ELF.txt"
 if grep -Eq 'Type: *DYN' "$rep/HEADER_ELF.txt" && \
    grep -Eq 'Machine:.*Advanced Micro Devices X86-64' "$rep/HEADER_ELF.txt" && \
    grep -Eq 'LOAD[[:space:]]' "$rep/SEGMENTOS_ELF.txt" && \
    grep -E 'Entry point address:[[:space:]]+0x[0-9a-fA-F]+' "$rep/HEADER_ELF.txt" | grep -Evq '0x0$'; then
   status=ELF_INTERMEDIARIO
   sha256sum "$out/smoke_8apis.elf" > "$rep/SHA256.txt"
 else
   echo 'Falha na validacao de cabecalhos ELF' >> "$rep/LINK.log"
 fi
fi
[[ -s "$rep/LINK.log" ]] || echo '(linker sem mensagens)' > "$rep/LINK.log"
python3 tools/etapa44/avaliar_link.py "$rep" "$status" SIM
# Falhar somente quando a tentativa aborta sem evidencia, nunca apresentar ELF falso.
test -s "$rep/RESULTADO.json" && test -s "$rep/APIS_DEFINIDAS.txt"
if [[ "$status" == ELF_INTERMEDIARIO ]]; then
 echo 'ELF_INTERMEDIARIO=SIM (sem eboot/PKG, nao testado no PS4)'
else
 echo 'ELF_INTERMEDIARIO=NAO: consulte LINK.log e SIMBOLOS_NAO_RESOLVIDOS.txt'
fi
