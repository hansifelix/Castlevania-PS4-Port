#!/usr/bin/env bash
# Kazuma Port Games BR — Etapa 12: compilacao, conversao e pacote de HOME BREW INDEPENDENTE.
# Este script roda em runner Linux de CI, NAO no PS4. Nada e instalado no console.
set -euo pipefail
if (( $# != 3 )); then
  echo 'Uso: compilar_homebrew_pkg.sh <OpenOrbis PS4Toolchain> <fonte do OpenOrbis> <fonte create-fself>' >&2
  exit 2
fi
sdk="$(cd "$1" && pwd)"
samples="$(cd "$2" && pwd)"
converter="$(cd "$3" && pwd)"
root="$(pwd)"
out="$root/relatorios/etapa13"
release="$root/release/etapa13"
mkdir -p "$out" "$release"

for cmd in clang++ ld.lld readelf python3 go sha256sum; do
  command -v "$cmd" >/dev/null || { echo "FERRAMENTA AUSENTE: $cmd" >&2; exit 2; }
done
for file in "$sdk/link.x" "$sdk/lib/crt1.o" \
            "$samples/samples/_common/graphics.cpp" \
            "$samples/samples/_common/graphics.h" \
            "$samples/samples/_common/log.h" \
            "$converter/cmd/create-fself/go-linux.mod" \
            'tools/etapa13/tela_kazuma.cpp' \
            'tools/etapa12/assets/icon0.png'; do
  test -s "$file" || { echo "ERRO: arquivo necessario ausente: $file" >&2; exit 3; }
done
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/pkgroot/sce_sys"

printf '[1/6] Compilando fonte livre de interface de video e nossa tela...\n'
flags=(--target=x86_64-pc-freebsd12-elf -std=c++17 -O1 -fPIC -funwind-tables \
  -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE \
  -isysroot "$sdk" -isystem "$sdk/include" -isystem "$sdk/include/c++/v1" \
  -I"$samples/samples/_common")
clang++ "${flags[@]}" -c tools/etapa13/tela_kazuma.cpp -o "$scratch/main.o" \
  >"$out/compilar_app.stdout.txt" 2>"$out/compilar_app.stderr.txt" || {
  cat "$out/compilar_app.stderr.txt" >&2; exit 1;
}
clang++ "${flags[@]}" -c "$samples/samples/_common/graphics.cpp" -o "$scratch/graphics.o" \
  >"$out/compilar_grafico.stdout.txt" 2>"$out/compilar_grafico.stderr.txt" || {
  cat "$out/compilar_grafico.stderr.txt" >&2; exit 1;
}

printf '[2/6] Ligando ELF minimo C++ (grafico CPU / SceVideoOut)...\n'
ld.lld -m elf_x86_64 -pie --script "$sdk/link.x" --eh-frame-hdr \
  -L"$sdk/lib" -o "$scratch/kazuma_12.elf" \
  "$sdk/lib/crt1.o" "$scratch/main.o" "$scratch/graphics.o" \
  -lc -lkernel -lc++ -lSceVideoOut -lScePad -lSceUserService -lSceSystemService -lSceSysmodule \
  >"$out/link.stdout.txt" 2>"$out/link.stderr.txt" || {
  cat "$out/link.stderr.txt" >&2; exit 1;
}
readelf -h "$scratch/kazuma_12.elf" > "$out/elf_header.txt"
readelf -W -d "$scratch/kazuma_12.elf" > "$out/elf_dynamic.txt" || true

printf '[3/6] Compilando conversor OpenOrbis fixado por commit...\n'
(
  cd "$converter/cmd/create-fself"
  go build -modfile=go-linux.mod -o "$scratch/create-fself" .
) >"$out/conversor_build.stdout.txt" 2>"$out/conversor_build.stderr.txt" || {
  cat "$out/conversor_build.stderr.txt" >&2; exit 1;
}

printf '[4/6] Criando OELF e eboot.bin experimental para este homebrew...\n'
OO_PS4_TOOLCHAIN="$sdk" "$scratch/create-fself" \
  -in "$scratch/kazuma_12.elf" -out "$scratch/kazuma_12.oelf" \
  -eboot "$scratch/pkgroot/eboot.bin" \
  >"$out/converter.stdout.txt" 2>"$out/converter.stderr.txt" || {
  cat "$out/converter.stdout.txt" "$out/converter.stderr.txt" >&2; exit 1;
}
test -s "$scratch/kazuma_12.oelf"
test -s "$scratch/pkgroot/eboot.bin"
cp tools/etapa12/assets/icon0.png "$scratch/pkgroot/sce_sys/icon0.png"
# KAZUMA_TESTE_PKG_REVISADO_START
# O primeiro PKG tinha apenas eboot, icon0 e param.sfo. Reproduzir estrutura
# de empacotamento dos exemplos OpenOrbis para diagnosticar erro no PS4.
mkdir -p "$scratch/pkgroot/sce_sys/about" "$scratch/pkgroot/sce_module"
right_file="$(find "$sdk" -type f -name right.sprx -print -quit)"
if [[ -z "$right_file" ]]; then
  echo 'FALHA: right.sprx nao encontrado no SDK. Abortando em vez de gerar pacote incompleto.' >&2
  exit 1
fi
cp "$right_file" "$scratch/pkgroot/sce_sys/about/right.sprx"
echo "Incluido sce_sys/about/right.sprx"
for module in libc.prx libSceFios2.prx; do
  module_path="$(find "$sdk" -type f -name "$module" -print -quit)"
  if [[ -n "$module_path" ]]; then
    cp "$module_path" "$scratch/pkgroot/sce_module/$module"
    echo "Incluido sce_module/$module (modulo publico do SDK)"
  else
    echo "AVISO: $module nao encontrado no SDK; verificacao de runtime ainda pendente."
  fi
done
# KAZUMA_TESTE_PKG_REVISADO_END

printf '[5/6] Construindo param.sfo + projeto .gp4 + pacote .pkg...\n'
# KAZUMA_ETAPA12_LIBSSL_COMPAT_START
# O PkgTool.Core do SDK usa .NET legado e nao carrega apenas libssl3 no Ubuntu 24.04.
# Extraimos libssl 1.1 em pasta TEMPORARIA; NAO instalamos no runner, celular ou PS4.
# A copia vem de pacote oficial do Ubuntu 20.04 (arquivo de seguranca 2025).
# Somente esta etapa efemera de empacotamento usa a biblioteca de compatibilidade.
echo '[5/6] Preparando biblioteca de compatibilidade do empacotador OpenOrbis...'
command -v dpkg-deb >/dev/null || { echo 'dpkg-deb ausente no runner' >&2; exit 1; }
mkdir -p "$scratch/ssl11"
curl --fail --silent --show-error --location --retry 3 --retry-delay 2 \
  'https://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2.24_amd64.deb' \
  -o "$scratch/libssl11.deb"
dpkg-deb -x "$scratch/libssl11.deb" "$scratch/ssl11"
legacy_ssl="$scratch/ssl11/usr/lib/x86_64-linux-gnu"
test -s "$legacy_ssl/libssl.so.1.1" || { echo 'Compatibilidade OpenSSL1.1 nao encontrada' >&2; exit 1; }
test -s "$legacy_ssl/libcrypto.so.1.1" || { echo 'Compatibilidade libcrypto1.1 nao encontrada' >&2; exit 1; }
export LD_LIBRARY_PATH="$legacy_ssl${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
# KAZUMA_ETAPA12_LIBSSL_COMPAT_END
packager="$sdk/bin/linux/PkgTool.Core"
gp4tool="$sdk/bin/linux/create-gp4"
for file in "$packager" "$gp4tool"; do
  test -f "$file" || { echo "Falta ferramenta do SDK: $file" >&2; exit 1; }
  chmod +x "$file" || true
done
TITLE_ID='BREW91235'
CONTENT_ID='IV0000-BREW91235_00-KAZUMAPADTEST000'
TITLE='Kazuma Port Games BR - Test 02'
VERSION='1.01'
pkgroot="$scratch/pkgroot"
(
  cd "$pkgroot"
  "$packager" sfo_new sce_sys/param.sfo
  "$packager" sfo_setentry sce_sys/param.sfo APP_TYPE --type Integer --maxsize 4 --value 1
  "$packager" sfo_setentry sce_sys/param.sfo APP_VER --type Utf8 --maxsize 8 --value "$VERSION"
  "$packager" sfo_setentry sce_sys/param.sfo ATTRIBUTE --type Integer --maxsize 4 --value 0
  "$packager" sfo_setentry sce_sys/param.sfo CATEGORY --type Utf8 --maxsize 4 --value 'gd'
  "$packager" sfo_setentry sce_sys/param.sfo CONTENT_ID --type Utf8 --maxsize 48 --value "$CONTENT_ID"
  "$packager" sfo_setentry sce_sys/param.sfo DOWNLOAD_DATA_SIZE --type Integer --maxsize 4 --value 0
  "$packager" sfo_setentry sce_sys/param.sfo SYSTEM_VER --type Integer --maxsize 4 --value 0
  "$packager" sfo_setentry sce_sys/param.sfo TITLE --type Utf8 --maxsize 128 --value "$TITLE"
  "$packager" sfo_setentry sce_sys/param.sfo TITLE_ID --type Utf8 --maxsize 12 --value "$TITLE_ID"
  "$packager" sfo_setentry sce_sys/param.sfo VERSION --type Utf8 --maxsize 8 --value "$VERSION"
  pkg_files=(eboot.bin sce_sys/param.sfo sce_sys/icon0.png sce_sys/about/right.sprx)
  for module in libc.prx libSceFios2.prx; do
    if [[ -s "sce_module/$module" ]]; then pkg_files+=("sce_module/$module"); fi
  done
  printf '%s\n' "${pkg_files[@]}" > "$out/manifesto_pkg.txt"
  "$gp4tool" -out pkg.gp4 --content-id="$CONTENT_ID" --files "${pkg_files[*]}"
  "$packager" pkg_build pkg.gp4 .
) >"$out/empacotar.stdout.txt" 2>"$out/empacotar.stderr.txt" || {
  cat "$out/empacotar.stdout.txt" "$out/empacotar.stderr.txt" >&2; exit 1;
}

pkg_path="$(find "$scratch/pkgroot" -type f -name '*.pkg' -print -quit)"
if [[ -z "$pkg_path" || ! -s "$pkg_path" ]]; then
  echo 'FALHA: empacotador finalizou, mas nenhum PKG foi localizado.' >&2
  exit 1
fi
cp "$pkg_path" "$release/${CONTENT_ID}.pkg"

printf '[6/6] Auditando PKG e salvando relatorios...\n'
python3 - "$scratch/kazuma_12.elf" "$scratch/kazuma_12.oelf" \
  "$scratch/pkgroot/eboot.bin" "$release/${CONTENT_ID}.pkg" "$out" <<'PY_CHECK'
from pathlib import Path
import hashlib, json, sys
elf, oelf, eboot, pkg, out = map(Path, sys.argv[1:])
def info(path):
    x = path.read_bytes()
    return {'tamanho_bytes':len(x), 'sha256':hashlib.sha256(x).hexdigest(), 'prefixo_hex':x[:16].hex()}
result = {
    'etapa':13, 'alvo':'PS4 Slim (Teste 02 de controle/memoria NAO executado no hardware)',
    'codigo_proprio':True, 'codigo_comercial_castlevania':False,
    'elf':info(elf), 'oelf':info(oelf), 'eboot_bin':info(eboot), 'pkg':info(pkg),
    'elf_header_ok':elf.read_bytes()[:4]==b'\x7fELF',
    'oelf_header_ok':oelf.read_bytes()[:4]==b'\x7fELF',
    'fself_header_ok':eboot.read_bytes()[:4]==bytes.fromhex('4f153d1d'),
    'teste_no_console':False, 'tela_apareceu_no_console':False,
    'pacote_gerado_sem_instalacao':True,
    'teste_controle_no_ps4':False, 'teste_memoria_no_ps4':False,
    'observacao':'PKG produzido offline: estrutura, instalacao e execucao no PS4 requerem teste em hardware. A mera geracao nao comprova funcionamento.'
}
(out/'resumo.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if not all(result[k] for k in ('elf_header_ok','oelf_header_ok','fself_header_ok')):
    raise SystemExit('FALHA: cabecalho inesperado nos binarios intermediarios')
if result['pkg']['tamanho_bytes'] < 1000:
    raise SystemExit('FALHA: PKG anormalmente pequeno')
print('COMPILACAO / LINK / CONVERSAO / EMPACOTAMENTO OFFLINE: CONCLUIDOS')
print('PKG:', pkg.name, result['pkg']['tamanho_bytes'],'bytes')
print('NAO FOI INSTALADO OU TESTADO NO PS4. NAO CONTEM CASTLEVANIA.')
PY_CHECK
