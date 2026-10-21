#!/usr/bin/env bash
# Kazuma Port Games BR — Etapa 6: auditoria offline de ligacao parcial.
# Entradas: quatro objetos ELF publicos ja compilados para alvo PS4 na Etapa 5.
# Nao cria eboot, PKG, ROM, jogo ou binario executavel.
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo 'Uso: bash auditar_ligacao.sh <diretorio_objetos> <diretorio_relatorio>' >&2
  exit 2
fi
objects_dir="$1"
report_dir="$2"
mkdir -p "$report_dir"

for command_name in ld.lld readelf nm python3 sha256sum; do
  command -v "$command_name" >/dev/null || { echo "Ferramenta ausente: $command_name" >&2; exit 2; }
done

names=(perfil_castlevania selecao_gpu controle_threads servico_info)
objects=()
for name in "${names[@]}"; do
  file="$objects_dir/$name.o"
  test -s "$file" || { echo "Objeto ausente: $file" >&2; exit 3; }
  readelf -h "$file" > "$report_dir/${name}_elf.txt"
  grep -Eq 'Type:[[:space:]]*REL' "$report_dir/${name}_elf.txt" || { echo "Objeto nao relocavel: $name" >&2; exit 3; }
  grep -Eq 'Machine:[[:space:]]*Advanced Micro Devices X86-64' "$report_dir/${name}_elf.txt" || { echo "Objeto nao x86_64: $name" >&2; exit 3; }
  nm --format=posix --undefined-only "$file" > "$report_dir/${name}_indefinidos.txt"
  nm --format=posix --defined-only "$file" > "$report_dir/${name}_definidos.txt"
  objects+=("$file")
done

# Unir apenas de forma relocavel. Nao fazemos o link final de um executavel.
ld.lld -m elf_x86_64 -r "${objects[@]}" -o "$report_dir/runtime_parcial_relocavel.o"
test -s "$report_dir/runtime_parcial_relocavel.o"
readelf -h "$report_dir/runtime_parcial_relocavel.o" > "$report_dir/parcial_elf.txt"
grep -Eq 'Type:[[:space:]]*REL' "$report_dir/parcial_elf.txt"
grep -Eq 'Machine:[[:space:]]*Advanced Micro Devices X86-64' "$report_dir/parcial_elf.txt"
nm --format=posix --undefined-only "$report_dir/runtime_parcial_relocavel.o" > "$report_dir/parcial_indefinidos.txt"
nm --format=posix --defined-only "$report_dir/runtime_parcial_relocavel.o" > "$report_dir/parcial_definidos.txt"
nm -C --undefined-only "$report_dir/runtime_parcial_relocavel.o" > "$report_dir/parcial_indefinidos_legiveis.txt"
readelf --wide --symbols "$report_dir/runtime_parcial_relocavel.o" > "$report_dir/parcial_simbolos_elf.txt"
sha256sum "$report_dir/runtime_parcial_relocavel.o" > "$report_dir/parcial_sha256.txt"

python3 - "$report_dir" "${names[@]}" <<'PY_KAZUMA_AUDIT'
from pathlib import Path
from collections import Counter
import json
import sys

root = Path(sys.argv[1])
names = sys.argv[2:]

def parse_symbols(path):
    # nm --format=posix prints '<mangled_name> <symbol_type> [value] [size]'.
    syms = []
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        parts = line.split()
        if len(parts) >= 2:
            syms.append({'name': parts[0], 'type': parts[1]})
    return syms

modules = {}
for name in names:
    imported = parse_symbols(root / f'{name}_indefinidos.txt')
    defined = parse_symbols(root / f'{name}_definidos.txt')
    modules[name] = {
        'undefined_count': len(imported),
        'defined_count': len(defined),
        'undefined_symbols': sorted({s['name'] for s in imported}),
    }

partial = parse_symbols(root / 'parcial_indefinidos.txt')
unique_unresolved = sorted({sym['name'] for sym in partial})
# A listagem de simbolos ainda indefinidos representa trabalho futuro:
# referencias C++, sistema, kernel, OpenOrbis etc. Nao e falha deste teste.
report = {
    'etapa': 6,
    'modo': 'ligacao ELF relocavel (-r), sem link final',
    'resultado': 'PASSOU: quatro objetos reunidos em ELF relocavel x86_64',
    'comprovacao_de_execucao_no_ps4': False,
    'comprovacao_de_jogo': False,
    'modulos': modules,
    'parcial': {
        'undefined_count': len(partial),
        'undefined_unique_count': len(unique_unresolved),
        'undefined_symbols': unique_unresolved,
    }
}
(root / 'resumo.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print('Auditoria de ligacao relocavel: OK')
for name, value in modules.items():
    print(f'  {name}: {value["undefined_count"]} referencias indefinidas')
print(f'  Combinacao: {len(unique_unresolved)} simbolos distintos ainda indefinidos')
print('  NAO ha link final, eboot, PKG ou prova de execucao do jogo.')
PY_KAZUMA_AUDIT

# Retemos no artefato apenas os relatorios, nao a copia reunida do codigo.
rm -f "$report_dir/runtime_parcial_relocavel.o"
test -s "$report_dir/resumo.json"
echo 'ETAPA 6: auditoria concluida sem gerar jogo, PKG ou executavel.'
