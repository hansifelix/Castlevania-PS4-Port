#!/usr/bin/env bash
# Kazuma Port Games BR — Etapa 7: compilar candidatos PUBLICOS a provedores do runtime.
# Requer a Etapa 5 já executada no mesmo job, para obter quatro objetos ELF relocaveis.
# Nao gera executavel, eboot, PKG, jogo ou arquivo comercial.
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo 'Uso: auditar_provedores.sh <sdk_openorbis> <upstream_publico>' >&2
  exit 2
fi
sdk="$1"; upstream="$2"
base='relatorios/etapa5/objetos'
out='relatorios/etapa7'
mkdir -p "$out/objetos"
for name in perfil_castlevania selecao_gpu controle_threads servico_info; do
  test -s "$base/$name.o" || { echo "Objeto da etapa 5 ausente: $name" >&2; exit 3; }
done

# Identificar símbolos indefinidos nos quatro objetos do experimento anterior.
ld.lld -m elf_x86_64 -r \
  "$base/perfil_castlevania.o" "$base/selecao_gpu.o" \
  "$base/controle_threads.o" "$base/servico_info.o" \
  -o "$out/quatro_componentes.o"
nm --format=posix --undefined-only "$out/quatro_componentes.o" > "$out/baseline_indefinidos.txt"
readelf -h "$out/quatro_componentes.o" > "$out/baseline_elf.txt"

# Candidatos sao fontes originais do projeto publico, nao implementacoes fabricadas.
names=(kernel memoria loader)
paths=(runtime/src/kernel.cpp runtime/src/memory.cpp runtime/src/loader.cpp)
common=(
  --target=x86_64-pc-freebsd12-elf
  -std=c++20 -D_POSIX_C_SOURCE=200809L
  -fPIC -fno-exceptions -funwind-tables -O1
  -isysroot "$sdk"
  -isystem "$sdk/include"
  -isystem "$sdk/include/c++/v1"
  -I "$upstream/runtime/include"
  -I "$upstream/runtime/src"
  -I "$upstream/runtime/src/nvn"
)
printf 'fonte\tcompilacao\n' > "$out/compilacao.tsv"
objs=(
  "$base/perfil_castlevania.o" "$base/selecao_gpu.o"
  "$base/controle_threads.o" "$base/servico_info.o"
)
failures=0
for i in "${!names[@]}"; do
  name="${names[$i]}"; input="$upstream/${paths[$i]}"; obj="$out/objetos/$name.o"
  echo "[ETAPA7] Compilando provedor PUBLICO: ${paths[$i]}"
  # Teste isolado: no OpenOrbis, libc++ referencia vasprintf sem declaracao
  # visivel ao compilar loader.cpp com _POSIX_C_SOURCE=200809L.
  # Apenas declaramos a interface, sem implementacao inventada e sem link final.
  extra_flags=()
  if [[ "$name" == loader ]]; then
    compat_header="$out/kazuma_loader_vasprintf_compat.h"
    cat > "$compat_header" <<'KAZUMA_VASPRINTF_HEADER'
#include <stdarg.h>
#ifdef __cplusplus
extern "C" {
#endif
int vasprintf(char **, const char *, va_list);
#ifdef __cplusplus
}
#endif
KAZUMA_VASPRINTF_HEADER
    extra_flags=(-include "$compat_header")
  fi
  if clang++ "${common[@]}" "${extra_flags[@]}" -c "$input" -o "$obj" > "$out/$name.log" 2>&1; then
    if ! readelf -h "$obj" > "$out/${name}_elf.txt" || \
       ! grep -Eq 'Type:[[:space:]]*REL' "$out/${name}_elf.txt" || \
       ! grep -Eq 'Machine:[[:space:]]*Advanced Micro Devices X86-64' "$out/${name}_elf.txt"; then
      echo "ERRO: formato ELF inesperado: $name" >&2
      printf '%s\tFALHA_ELF\n' "$name" >> "$out/compilacao.tsv"
      failures=$((failures+1))
      rm -f "$obj"
    else
      printf '%s\tPASS\n' "$name" >> "$out/compilacao.tsv"
      nm --format=posix --defined-only "$obj" > "$out/${name}_definidos.txt"
      objs+=("$obj")
    fi
  else
    printf '%s\tFALHA_COMPILACAO\n' "$name" >> "$out/compilacao.tsv"
    failures=$((failures+1))
    echo "Nao compilou: $name (consulte $out/$name.log)"
    tail -n 18 "$out/$name.log" || true
  fi
done

# Auditoria dos simbolos que cada candidato pode fornecer. Nao declara link final.
python3 - "$out" <<'PY'
from pathlib import Path
import json, sys
root = Path(sys.argv[1])
def names(path):
    result=set()
    for ln in path.read_text(encoding='utf-8', errors='replace').splitlines():
        parts=ln.split()
        if len(parts)>=2:result.add(parts[0])
    return result
baseline=names(root/'baseline_indefinidos.txt')
providers={}
for candidate in ('kernel','memoria','loader'):
    path=root/f'{candidate}_definidos.txt'
    if path.exists(): providers[candidate]=names(path)
coverage={s:[n for n,syms in providers.items() if s in syms] for s in sorted(baseline)}
found={s:p for s,p in coverage.items() if p}
missing=[s for s,p in coverage.items() if not p]
report={'etapa':7,'tipo':'auditoria de simbolos do runtime publico, sem executavel',
        'baseline_indefinidos':len(baseline),'simbolos_cobertos_pelos_provedores_compilados':len(found),
        'simbolos_restantes_sem_provedor_neste_teste':len(missing),
        'provedores_compilados':sorted(providers),
        'providos':found,'nao_providos':missing,
        'comprovacao_de_execucao_PS4':False,'comprovacao_de_jogo':False}
(root/'resumo.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('Relatorio: baseline=%d, cobertos=%d, restantes=%d' % (len(baseline),len(found),len(missing)))
print('ATENCAO: C++/libc/ABI ainda requerem ligacao apropriada com o SDK.')
PY

# Teste parcial adicional com todos os provedores que compilaram.
if ld.lld -m elf_x86_64 -r "${objs[@]}" -o "$out/com_provedores.o" > "$out/ligacao_parcial.log" 2>&1; then
  readelf -h "$out/com_provedores.o" > "$out/com_provedores_elf.txt"
  nm --format=posix --undefined-only "$out/com_provedores.o" > "$out/com_provedores_indefinidos.txt"
  echo '[ETAPA7] Ligacao ELF relocavel com candidatos compilados: PASS'
else
  echo '[ETAPA7] Ligacao ELF relocavel com candidatos: FALHA. Consulte ligacao_parcial.log' >&2
  failures=$((failures+1))
fi
# Não entregar objetos binarios para usuario: apenas logs e mapas dos simbolos.
rm -f "$out/quatro_componentes.o" "$out/com_provedores.o"
if [[ "${KAZUMA_ETAPA8_GUARDAR_OBJETOS:-0}" != 1 ]]; then
  rm -rf "$out/objetos"
fi
cat "$out/compilacao.tsv"
if (( failures > 0 )); then
  echo "ETAPA7: falhas reais detectadas ($failures); CI deve ficar vermelho." >&2
  exit 1
fi
printf 'ETAPA7: tres provedores compilaram; mapas de dependencias salvos. SEM EXECUTAVEL.\n'
