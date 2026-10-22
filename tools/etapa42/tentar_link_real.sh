#!/usr/bin/env bash
# Etapa 42: tenta LINK FINAL ESTRITO do objeto runtime + bibliotecas OpenOrbis.
# Nao injeta stubs e nao ignora simbolos indefinidos. O fracasso do link e
# um resultado tecnico esperado, salvo em diagnostico legivel. SEM PKG.
set -euo pipefail
: "${OO_PS4_TOOLCHAIN:?SDK nao configurado}"
: "${RUNNER_TEMP:?Somente GitHub Actions}"

sdk="$OO_PS4_TOOLCHAIN"
out="$RUNNER_TEMP/kazuma39"
rep="relatorios/etapa42"
mkdir -p "$rep"
obj="$out/runtime_etapa41_partial.o"
test -s "$obj" || { echo 'Falta objeto integrado da Etapa 41' >&2; exit 2; }
test -s "$sdk/link.x" && test -s "$sdk/lib/crt1.o" || {
  echo 'OpenOrbis incompleto: link.x ou crt1.o ausente' >&2; exit 3;
}

printf '[42/1] Teste independente: SDK consegue linkar ELF homebrew minimo?\n'
if bash tools/etapa10/testar_link_homebrew.sh "$sdk" > "$rep/BASELINE_HOME_BREW.log" 2>&1; then
  baseline=PASSOU
else
  baseline=FALHOU
fi
printf 'BASELINE_SDK=%s\n' "$baseline"

printf '[42/2] Verificar bibliotecas OpenOrbis disponiveis.\n'
find "$sdk/lib" -maxdepth 1 -type f \( -name '*.a' -o -name '*.so' \) -printf '%f\n' | LC_ALL=C sort > "$rep/INVENTARIO_BIBLIOTECAS.txt"
libs=()
# libc++ presente no SDK oficial, mas verificar em vez de inventar nome.
if [[ -s "$sdk/lib/libc++.a" ]]; then libs+=(-lc++); fi
libs+=(-lc -lkernel)
# libm opcional, dependendo do empacotamento OpenOrbis.
if [[ -s "$sdk/lib/libm.a" ]]; then libs+=(-lm); fi
printf '%s\n' "${libs[@]}" > "$rep/LIBS_USADAS.txt"

printf '[42/3] Tentar link ELF FINAL. Falha nao sera ocultada como sucesso.\n'
# Ativamos crt1, entrada real, bibliotecas SDK. Sem --allow-shlib-undefined,
# --unresolved-symbols=ignore-all, stubs falsos nem remover codigo do runtime.
# Limite de diagnosticos evita log gigantesco; consulte simbolos restantes etapa41.
status=FALHOU_LINK_ESTRITO
if ld.lld-18 -m elf_x86_64 -pie --script "$sdk/link.x" \
    --eh-frame-hdr --error-limit=350 -L"$sdk/lib" \
    -o "$out/kazuma42_tentativa.elf" \
    "$sdk/lib/crt1.o" "$obj" \
    --start-group "${libs[@]}" --end-group \
    > "$rep/LINK_EXECUTAVEL.log" 2>&1; then
  readelf -W -h "$out/kazuma42_tentativa.elf" > "$rep/ELF_HEADER.txt"
  readelf -W -l "$out/kazuma42_tentativa.elf" > "$rep/ELF_PROGRAM_HEADERS.txt"
  # ELF so sera reportado como produzido se houver segmentos e entrada!
  if grep -Eq 'Type:[[:space:]]*DYN' "$rep/ELF_HEADER.txt" && \
     grep -Eq 'Machine:.*Advanced Micro Devices X86-64' "$rep/ELF_HEADER.txt" && \
     grep -Eq 'LOAD[[:space:]]' "$rep/ELF_PROGRAM_HEADERS.txt" && \
     grep -E 'Entry point address:[[:space:]]+0x[0-9a-fA-F]+' "$rep/ELF_HEADER.txt" | grep -Evq '0x0$'; then
    status=SUCESSO_ELF_INTERMEDIARIO
    sha256sum "$out/kazuma42_tentativa.elf" > "$rep/ELF_SHA256.txt"
  else
    echo 'O linker saiu 0, mas ELF intermediario nao passou na verificacao de tipo/segmentos.' >> "$rep/LINK_EXECUTAVEL.log"
  fi
fi
printf '[42/4] Interpretar resultado.\n'
python3 tools/etapa42/diagnosticar_link.py "$rep" --status "$status" --baseline "$baseline" --libs="${libs[*]}"
head -n 28 "$rep/LEIA_PRIMEIRO.txt"

# Verificacoes de integridade. Link estrito falhar e aceitavel em etapa diagnostica,
# mas so se houver log explicito. Ausencia de log ou inconsistencias falham o CI.
test -s "$rep/RESUMO.json" && test -s "$rep/LEIA_PRIMEIRO.txt"
if [[ "$status" == FALHOU_LINK_ESTRITO ]]; then
  test -s "$rep/LINK_EXECUTAVEL.log" || {
    echo 'ERRO: link falhou sem log. Marcar CI vermelho.' >&2; exit 1;
  }
  echo 'Diagnostico completo; ELF executavel do runtime AINDA NAO foi gerado.'
else
  echo 'Link produziu ELF INTERMEDIARIO x86-64; NAO e um eboot nem comprovacao no PS4.'
fi
if [[ "$baseline" == FALHOU ]]; then
  echo 'ATENCAO: teste de ELF homebrew minimo do SDK falhou; verificar BASELINE_HOME_BREW.log.'
fi
