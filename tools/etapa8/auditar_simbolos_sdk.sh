#!/usr/bin/env bash
# Kazuma Port Games BR — Etapa 8: auditoria offline de sete objetos reais do runtime publico.
# Nao cria eboot, PKG ou executavel. Nao altera o SDK nem a fonte upstream.
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo 'Uso: auditar_simbolos_sdk.sh <diretorio_OpenOrbis_PS4Toolchain>' >&2
  exit 2
fi
sdk="$1"
base='relatorios/etapa5/objetos'
extra='relatorios/etapa7/objetos'
out='relatorios/etapa8'
mkdir -p "$out"
for cmd in ld.lld readelf nm python3; do
  command -v "$cmd" >/dev/null || { echo "Faltando ferramenta: $cmd" >&2; exit 2; }
done
test -d "$sdk/lib" || { echo "Pasta lib do SDK ausente: $sdk/lib" >&2; exit 2; }
base_objs=("$base/perfil_castlevania.o" "$base/selecao_gpu.o" "$base/controle_threads.o" "$base/servico_info.o")
provider_objs=("$extra/kernel.o" "$extra/memoria.o" "$extra/loader.o")
for obj in "${base_objs[@]}" "${provider_objs[@]}"; do
  test -s "$obj" || { echo "Objeto ELF ausente: $obj" >&2; exit 3; }
  elf="$(readelf -h "$obj")"
  grep -Eq 'Type:[[:space:]]*REL' <<< "$elf" || { echo "Nao ET_REL: $obj" >&2; exit 3; }
  grep -Eq 'Machine:[[:space:]]*Advanced Micro Devices X86-64' <<< "$elf" || { echo "Nao ELF x86_64: $obj" >&2; exit 3; }
done
ld.lld -m elf_x86_64 -r "${base_objs[@]}" -o "$out/base4.o"
ld.lld -m elf_x86_64 -r "${base_objs[@]}" "${provider_objs[@]}" -o "$out/combinado7.o"
readelf -h "$out/combinado7.o" > "$out/objeto7_elf.txt"
nm --format=posix --undefined-only "$out/base4.o" > "$out/base4_indefinidos.txt"
nm --format=posix --undefined-only "$out/combinado7.o" > "$out/combinado7_indefinidos.txt"
nm -C --undefined-only "$out/combinado7.o" > "$out/combinado7_legiveis.txt"
nm --format=posix --defined-only "$out/combinado7.o" > "$out/combinado7_definidos.txt"
python3 - "$sdk" "$out" <<'PY_KAZUMA_ANALYZE'
from pathlib import Path
from collections import defaultdict
import json, subprocess, sys
sdk, out = Path(sys.argv[1]), Path(sys.argv[2])
def syms(path):
    result=set()
    for ln in path.read_text(encoding='utf-8',errors='replace').splitlines():
        parts=ln.split()
        if len(parts)>=2 and len(parts[1])==1: result.add(parts[0])
    return result
before=syms(out/'base4_indefinidos.txt')
after=syms(out/'combinado7_indefinidos.txt')
resolved=sorted(before-after)
new=sorted(after-before)
static_libs=sorted((sdk/'lib').rglob('*.a'))
providers=defaultdict(list)
scan_errors=[]
# Diagnostico de disponibilidade de simbolos em arquivos estaticos do SDK.
# Um simbolo encontrado NAO significa que o link final sera possivel.
for library in static_libs:
    proc=subprocess.run(['nm','-P','-g','--defined-only',str(library)],capture_output=True,text=True,errors='replace')
    if proc.returncode not in (0,None):
        scan_errors.append(library.name)
    for ln in proc.stdout.splitlines():
        parts=ln.split()
        if len(parts)>=2 and len(parts[1])==1 and parts[0] in after:
            label=str(library.relative_to(sdk))
            if label not in providers[parts[0]]: providers[parts[0]].append(label)
report={
 'etapa':8,
 'tipo':'auditoria de sete objetos publicos e arquivos .a do SDK; sem link final',
 'numero_objetos':7,
 'elf_relocavel_x86_64':True,
 'base4_indefinidos':len(before),
 'combinado7_indefinidos':len(after),
 'resolvidos_com_provedores':len(resolved),
 'resolvidos':resolved,
 'novos_indefinidos_apos_adicionar_provedores':len(new),
 'novos_indefinidos':new,
 'indefinidos_restantes':sorted(after),
 'arquivos_estaticos_sdk_examinados':len(static_libs),
 'simbolos_indefinidos_encontrados_em_arquivos_estaticos_sdk':len(providers),
 'possiveis_bibliotecas_por_simbolo':dict(sorted(providers.items())),
 'bibliotecas_com_avisos_durante_varredura':scan_errors,
 'comprovacao_de_link_final':False,
 'comprovacao_de_execucao_no_ps4':False,
 'comprovacao_de_jogo':False
}
(out/'resumo.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f"BASE 4: {len(before)} simbolos indefinidos")
print(f"COM 7: {len(after)} simbolos indefinidos")
print(f"Referencias antigas resolvidas: {len(resolved)}; novas adicionadas: {len(new)}")
print(f"Arquivos .a do SDK consultados: {len(static_libs)}; possiveis provedores: {len(providers)}")
print('IMPORTANTE: sem link final, eboot, PKG, recompilacao comercial ou teste no PS4.')
PY_KAZUMA_ANALYZE
# Nao distribuir objetos binarios; apenas diagnosticos e listas de simbolos.
rm -f "$out/base4.o" "$out/combinado7.o"
test -s "$out/resumo.json"
