#!/usr/bin/env bash
# Etapa 10 — gerar e analisar SOMENTE ELF intermediario, sem converter em eboot/PKG.
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo 'Uso: bash tools/etapa10/testar_link_homebrew.sh <PS4Toolchain>' >&2
  exit 2
fi
sdk="$(cd "$1" && pwd)"
out='relatorios/etapa10'
mkdir -p "$out"
for prog in clang ld.lld readelf nm sha256sum python3; do
  command -v "$prog" >/dev/null || { echo "Ferramenta ausente: $prog" >&2; exit 2; }
done
for file in "$sdk/link.x" "$sdk/lib/crt1.o" 'tools/etapa10/minimo_homebrew.c'; do
  test -s "$file" || { echo "Arquivo necessario ausente: $file" >&2; exit 3; }
done
# Artefatos executaveis de compilacao sao temporarios e NUNCA publicados no GitHub.
temp="$(mktemp -d)"
trap 'rm -rf "$temp"' EXIT

printf 'TESTE 1/3: compilar C independente para x86_64/FreeBSD ABI\n'
if ! clang --target=x86_64-pc-freebsd12-elf -O1 -fPIC -fno-stack-protector \
      -funwind-tables -isysroot "$sdk" -isystem "$sdk/include" \
      -c tools/etapa10/minimo_homebrew.c -o "$temp/main.o" \
      >"$out/compilar.stdout.txt" 2>"$out/compilar.stderr.txt"; then
  echo 'FALHA REAL DE COMPILACAO. Leia relatorios/etapa10/compilar.stderr.txt' >&2
  cat "$out/compilar.stderr.txt" >&2
  exit 1
fi
readelf -h "$temp/main.o" >"$out/objeto_elf.txt"
grep -Eq 'Type:[[:space:]]*REL' "$out/objeto_elf.txt" || { echo 'Objeto nao e ET_REL' >&2; exit 1; }
grep -Eq 'Machine:[[:space:]]*Advanced Micro Devices X86-64' "$out/objeto_elf.txt" || { echo 'Objeto nao e x86-64' >&2; exit 1; }

printf 'TESTE 2/3: tentar link ELF com crt1, libc e libkernel OpenOrbis\n'
# Argumentos inspirados nos exemplos publicos do OpenOrbis.
# Nao desabilitar erros de simbolos indefinidos artificialmente.
if ! ld.lld -m elf_x86_64 -pie --script "$sdk/link.x" --eh-frame-hdr \
      -L"$sdk/lib" -o "$temp/kazuma_minimo.elf" \
      "$sdk/lib/crt1.o" "$temp/main.o" -lc -lkernel \
      >"$out/link.stdout.txt" 2>"$out/link.stderr.txt"; then
  echo 'LINK ELF FALHOU: isto e um resultado diagnostico, nao e um ELF valido.' >&2
  cat "$out/link.stderr.txt" >&2
  exit 1
fi

printf 'TESTE 3/3: verificar formato, ponto de entrada e segmentos do ELF\n'
readelf -h "$temp/kazuma_minimo.elf" >"$out/link_elf_header.txt"
readelf -W -l "$temp/kazuma_minimo.elf" >"$out/link_program_headers.txt"
readelf -W -d "$temp/kazuma_minimo.elf" >"$out/link_dynamic.txt" || true
nm "$temp/kazuma_minimo.elf" >"$out/link_simbolos.txt" || true
sha256sum "$temp/kazuma_minimo.elf" >"$out/hash_elf.txt"
python3 - "$out" <<'PY_VALIDATE'
from pathlib import Path
import json, re, sys
out=Path(sys.argv[1]); h=(out/'link_elf_header.txt').read_text()
p=(out/'link_program_headers.txt').read_text()
# ET_DYN + x86_64 + entry nao-zero + PT_LOAD representam apenas um ELF
# ligado offline, NAO e um binario Sony executavel por um PS4.
type_ok = bool(re.search(r'Type:\s+DYN\b',h))
machine_ok = bool(re.search(r'Machine:\s+Advanced Micro Devices X86-64',h))
m = re.search(r'Entry point address:\s*(0x[0-9a-fA-F]+)',h)
entry = int(m.group(1),16) if m else 0
load_ok = bool(re.search(r'^\s+LOAD\s',p,re.MULTILINE))
report = {
 'etapa':10,
 'experimento':'homebrew C minimo independente; ligacao offline com OpenOrbis',
 'sdk':'OpenOrbis v0.5.4',
 'compilou_objeto_elf_x86_64': True,
 'ligacao_elf_concluida': True,
 'tipo_elf_dyn':type_ok,
 'arquitetura_x86_64':machine_ok,
 'entry_point_nao_zero':entry>0,
 'segmento_pt_load_presente':load_ok,
 'comprovacao_de_formato_sony_oelf':False,
 'comprovacao_de_execucao_no_ps4':False,
 'comprovacao_de_castlevania_funcional':False,
 'criou_eboot_ou_pkg':False
}
(out/'resumo.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if not all([type_ok,machine_ok,entry>0,load_ok]):
    raise SystemExit('FALHA: ELF ligado nao passou pela inspecao. Verifique relatorios.')
print('PASS: ELF intermediario x86-64 ET_DYN com ponto de entrada nao-zero.')
print('NAO comprova formato PS4 final nem execucao no console; sem eboot e sem PKG.')
PY_VALIDATE
