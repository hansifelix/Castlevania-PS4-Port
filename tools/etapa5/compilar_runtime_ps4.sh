#!/usr/bin/env bash
# Etapa 5: somente objetos relocaveis de fontes PUBLICOS originais do runtime.
# NUNCA produz PKG, eboot, instalador, arquivos de jogo ou empacotamento PS4.
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo 'Uso: bash compilar_runtime_ps4.sh <sdk> <codigo_upstream>' >&2
  exit 2
fi
sdk="$1"
upstream="$2"
log_dir='relatorios/etapa5'
mkdir -p "$log_dir" "$log_dir/objetos"
test -d "$sdk/include/c++/v1"
test -d "$upstream/runtime/src"

clang_flags=(
  --target=x86_64-pc-freebsd12-elf
  -std=c++20 -fPIC -fno-exceptions -funwind-tables -O1
  -isysroot "$sdk"
  -isystem "$sdk/include"
  -isystem "$sdk/include/c++/v1"
  -I "$upstream/runtime/include"
  -I "$upstream/runtime/src"
  -I "$upstream/runtime/src/nvn"
)

# Tres unidades da implementacao REAL do runtime e o perfil PUBLICO real do jogo.
# O teste GPU_PICK usa modo standalone: nao testa Vulkan nem renderizacao.
names=(perfil_castlevania selecao_gpu controle_threads servico_info)
paths=(
  games/castlevania/game.cpp
  runtime/src/nvn/nvn_gpu_pick.cpp
  runtime/src/kernel_thread_control.cpp
  runtime/src/svc_info.cpp
)

printf 'componente\tresultado\tobjeto_sha256\n' > "$log_dir/resultados.tsv"
failures=0
for i in "${!names[@]}"; do
  name="${names[$i]}"
  input="$upstream/${paths[$i]}"
  output="$log_dir/objetos/${name}.o"
  echo "[${i}/4] Compilando codigo original: ${paths[$i]}"
  test -s "$input" || { echo "Fonte ausente: $input" >&2; exit 3; }
  extra=()
  if [[ "$name" == selecao_gpu ]]; then
    extra=(-DNX_GPU_PICK_STANDALONE)
  fi
  if clang++ "${clang_flags[@]}" "${extra[@]}" -c "$input" -o "$output" > "$log_dir/${name}.txt" 2>&1; then
    if readelf -h "$output" > "$log_dir/${name}_elf.txt" && \
       grep -Eqi 'Machine:[[:space:]]*Advanced Micro Devices X86-64' "$log_dir/${name}_elf.txt" && \
       grep -Eqi 'Type:[[:space:]]*REL' "$log_dir/${name}_elf.txt"; then
      hash="$(sha256sum "$output" | awk '{print $1}')"
      printf '%s\tPASS\t%s\n' "$name" "$hash" >> "$log_dir/resultados.tsv"
      echo "PASS: $name (objeto ELF x86-64 relocavel; NAO executavel PS4)"
    else
      printf '%s\tFALHA_ELF\t-\n' "$name" >> "$log_dir/resultados.tsv"
      failures=$((failures+1))
      echo "FALHA: $name (formato ELF inesperado)" >&2
    fi
  else
    printf '%s\tFALHA_COMPILACAO\t-\n' "$name" >> "$log_dir/resultados.tsv"
    failures=$((failures+1))
    echo "FALHA: $name. Consulte $log_dir/${name}.txt" >&2
    cat "$log_dir/${name}.txt" >&2
  fi
done

cat "$log_dir/resultados.tsv"
if [[ $failures -ne 0 ]]; then
  echo "RESULTADO: ${failures} fonte(s) nao passaram. GitHub DEVE ficar vermelho." >&2
  exit 1
fi
# Falhar se nao existirem exatamente quatro linhas PASS, independentemente de outros logs.
[[ $(awk -F '\t' '$2=="PASS"{n++} END{print n+0}' "$log_dir/resultados.tsv") -eq 4 ]]
echo 'RESULTADO: 4/4 objetos reais de codigo publico compilados para alvo PS4; nao ha eboot, PKG ou jogo.'
