#!/usr/bin/env bash
# Etapa 11: converte unicamente um homebrew C independente para OELF/FSELF temporarios.
# Nao faz PKG, nao utiliza assets de jogos nem instala no PS4.
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo 'Uso: testar_fself_offline.sh <OpenOrbis/PS4Toolchain> <diretorio_openorbis_create-fself>' >&2
  exit 2
fi
sdk="$(cd "$1" && pwd)"
converter_source="$(cd "$2" && pwd)"
out='relatorios/etapa11'
mkdir -p "$out"
for prog in clang ld.lld go readelf python3 sha256sum; do
  command -v "$prog" >/dev/null || { echo "Ferramenta ausente: $prog" >&2; exit 2; }
done
for path in "$sdk/link.x" "$sdk/lib/crt1.o" tools/etapa10/minimo_homebrew.c "$converter_source/cmd/create-fself/go-linux.mod"; do
  test -s "$path" || { echo "Arquivo esperado nao encontrado: $path" >&2; exit 3; }
done
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

echo '[1/4] Compilando create-fself (fonte publica, revisao fixa)...'
(
  cd "$converter_source/cmd/create-fself"
  go build -modfile=go-linux.mod -o "$scratch/create-fself" .
) >"$out/conversor_build.stdout.txt" 2>"$out/conversor_build.stderr.txt" || {
  echo 'FALHA: compilacao do conversor. Veja conversor_build.stderr.txt' >&2
  cat "$out/conversor_build.stderr.txt" >&2
  exit 1
}
test -s "$scratch/create-fself"

echo '[2/4] Compilando e ligando o mesmo ELF minimo da etapa 10...'
if ! clang --target=x86_64-pc-freebsd12-elf -O1 -fPIC -fno-stack-protector \
      -funwind-tables -isysroot "$sdk" -isystem "$sdk/include" \
      -c tools/etapa10/minimo_homebrew.c -o "$scratch/main.o" \
      >"$out/compilar.stdout.txt" 2>"$out/compilar.stderr.txt"; then
  cat "$out/compilar.stderr.txt" >&2
  exit 1
fi
if ! ld.lld -m elf_x86_64 -pie --script "$sdk/link.x" --eh-frame-hdr \
      -L"$sdk/lib" -o "$scratch/kazuma_minimo.elf" \
      "$sdk/lib/crt1.o" "$scratch/main.o" -lc -lkernel \
      >"$out/link.stdout.txt" 2>"$out/link.stderr.txt"; then
  cat "$out/link.stderr.txt" >&2
  exit 1
fi
readelf -h "$scratch/kazuma_minimo.elf" >"$out/elf_intermediario_header.txt"

echo '[3/4] Convertendo para OELF e eboot.bin FSELF TEMPORARIOS...'
if ! OO_PS4_TOOLCHAIN="$sdk" "$scratch/create-fself" \
  -in "$scratch/kazuma_minimo.elf" \
  -out "$scratch/kazuma_minimo.oelf" \
  -eboot "$scratch/eboot.bin" \
  >"$out/converter.stdout.txt" 2>"$out/converter.stderr.txt"; then
  echo 'Conversor retornou falha. Nao afirmar que criou formato PS4.' >&2
  cat "$out/converter.stdout.txt" "$out/converter.stderr.txt" >&2
  exit 1
fi
for file in "$scratch/kazuma_minimo.oelf" "$scratch/eboot.bin"; do
  test -s "$file" || { echo "Arquivo de saida ausente: $file" >&2; exit 1; }
done
readelf -h "$scratch/kazuma_minimo.oelf" >"$out/oelf_header.txt" 2>"$out/oelf_readelf.stderr.txt" || true

echo '[4/4] Verificando assinatura de cabecalho e hashes (NAO teste no PS4)...'
python3 - "$scratch/kazuma_minimo.elf" "$scratch/kazuma_minimo.oelf" "$scratch/eboot.bin" "$out" <<'PY_KAZUMA_VALIDATE'
from pathlib import Path
import hashlib, json, sys
elf, oelf, fself, out=map(Path, sys.argv[1:])
def props(path):
    dat=path.read_bytes()
    return {'tamanho_bytes':len(dat),'sha256':hashlib.sha256(dat).hexdigest(), 'prefixo_hex':dat[:16].hex()}
a,b,c=map(props,[elf,oelf,fself])
elf_ok=elf.read_bytes()[:4]==b'\x7fELF'
oelf_ok=oelf.read_bytes()[:4]==b'\x7fELF'
# Primeiro valor no cabecalho SELF e 0x1D3D154F em little-endian.
fself_ok=fself.read_bytes()[:4]==bytes.fromhex('4f153d1d')
embedded_elf=fself.read_bytes().find(b'\x7fELF',4,8192)>=4
report={'etapa':11,'tipo':'diagnostico offline de OELF/fSELF homebrew minimo, sem jogo',
        'elf_original':a,'oelf_intermediario':b,'fself_eboot_temporario':c,
        'elf_magic_ok':elf_ok,'oelf_magic_ok':oelf_ok,'self_magic_ok':fself_ok,
        'self_contem_cabecalho_elf':embedded_elf,
        'teste_real_ps4':False,'comprovacao_execucao_ps4':False,
        'comprovacao_castlevania_portado':False,'pkg_criado':False,
        'executaveis_publicados':False}
(out/'resumo.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for k,v in [('ELF inicial',elf_ok),('OELF intermediario',oelf_ok),('SELF magic',fself_ok),('ELF embutido',embedded_elf)]:
    print(f'{k}: {"PASS" if v else "FALHA"}')
if not all((elf_ok,oelf_ok,fself_ok,embedded_elf)):
    raise SystemExit('O arquivo foi produzido, mas falhou a validacao do formato. Veja o relatorio.')
print('PASS: OELF e FSELF com cabecalhos coerentes (apenas offline).')
print('NAO comprova execucao no PS4; sem PKG, sem jogo.')
PY_KAZUMA_VALIDATE
