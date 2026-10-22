#!/usr/bin/env bash
# Etapa 43 - reproduzir e corrigir apenas o erro de ferramenta da Etapa 42.
# A Etapa 42 falhou no baseline pois 'ld.lld' nao estava no PATH;
# aqui usamos um alias local para 'ld.lld-18' sem modificar o sistema.
# Nao cria PKG, eboot nem executa o jogo. Nao inclui codigo comercial.
set -euo pipefail
: "${OO_PS4_TOOLCHAIN:?Defina o caminho do OpenOrbis PS4Toolchain}"
: "${RUNNER_TEMP:?Execute pelo GitHub Actions}"
sdk="$OO_PS4_TOOLCHAIN"
rep="relatorios/etapa43"
mkdir -p "$rep" "$RUNNER_TEMP/kazuma43-bin"
# Evita afirmar sucesso se o SDK nao tiver os artefatos indispensaveis.
for f in "$sdk/link.x" "$sdk/lib/crt1.o" "$sdk/lib/libc.a" "$sdk/lib/libkernel.so"; do
    test -s "$f" || { echo "ARQUIVO_SDK_AUSENTE=$f" | tee -a "$rep/STATUS.txt"; exit 2; }
done
: > "$rep/FERRAMENTAS.txt"
for prog in clang-18 ld.lld-18 llvm-nm-18 readelf nm python3; do
    path="$(command -v "$prog" || true)"
    echo "$prog=$path" >> "$rep/FERRAMENTAS.txt"
    test -n "$path" || { echo "Ferramenta ausente: $prog" >&2; exit 3; }
done
ln -sfn "$(command -v ld.lld-18)" "$RUNNER_TEMP/kazuma43-bin/ld.lld"
ln -sfn "$(command -v clang-18)" "$RUNNER_TEMP/kazuma43-bin/clang"
export PATH="$RUNNER_TEMP/kazuma43-bin:$PATH"
command -v ld.lld >> "$rep/FERRAMENTAS.txt"

printf '%s\n' 'CAUSA_ETAPA42_BASELINE=ld.lld ausente do PATH' > "$rep/STATUS.txt"
printf 'SOLUCAO_TESTADA=alias local para ld.lld-18\n' >> "$rep/STATUS.txt"
echo '[43/1] Testando ELF minimo original com ferramentas corretamente localizadas.'
if bash tools/etapa10/testar_link_homebrew.sh "$sdk" > "$rep/BASELINE_CORRIGIDO.log" 2>&1; then
    echo 'BASELINE_RESULTADO=PASSOU' | tee -a "$rep/STATUS.txt"
else
    echo 'BASELINE_RESULTADO=FALHOU' | tee -a "$rep/STATUS.txt"
fi

# Verifica existencia dos relatorios do script original. Ele executa em relatorios/etapa10.
if grep -q '^BASELINE_RESULTADO=PASSOU$' "$rep/STATUS.txt"; then
    test -s relatorios/etapa10/resumo.json || { echo 'Relatorio da baseline ausente' >&2; exit 4; }
    cp relatorios/etapa10/resumo.json "$rep/BASELINE_ELF_RESUMO.json"
else
    grep -Eq '(FALH|ausente|error:|undefined|Erro|erro)' "$rep/BASELINE_CORRIGIDO.log" || {
      echo 'Baseline falhou sem diagnostico claro' >&2; exit 5;
    }
fi

echo '[43/2] Verificando simbolo C++ TLS em bibliotecas reais do SDK.'
: > "$rep/PROVEDORES_TLS.txt"
for lib in libc++.a libc.a libkernel.a libm.a; do
   path="$sdk/lib/$lib"
   [[ -s "$path" ]] || continue
   echo "=== $lib ===" >> "$rep/PROVEDORES_TLS.txt"
   # Consulta SOMENTE a definicao; nao implementa comportamento falso.
   llvm-nm-18 --defined-only "$path" 2>/dev/null | grep -E '__cxa_thread_atexit_impl([[:space:]]|$)' \
     >> "$rep/PROVEDORES_TLS.txt" || true
done

cat > "$rep/RESUMO.txt" <<'EOF'
ETAPA 43 - BASELINE MINIMA E CLASSIFICACAO
A Etapa 42: BASELINE_HOME_BREW=FALHOU, porque 'ld.lld' nao estava no PATH.
A Etapa 42: LINK_EXECUTAVEL=FALHOU_LINK_ESTRITO (33 simbolos no log).
Consulte STATUS.txt e BASELINE_CORRIGIDO.log para saber o resultado DESTA etapa.
Se a baseline passar, isso valida SOMENTE o ELF minimo de teste, NAO o runtime e NAO o jogo.
O runtime completo segue exigindo 'main', simbolos nx::game e interfaces nx::plat.
Um check verde indica que o diagnostico foi executado, nao que o jogo funcione.
Sem ROM/NSP/APK/PKG/eboot, sem testes no console.
EOF
cat "$rep/STATUS.txt"
echo 'Etapa 43: classificacao tecnica pronta. Consultar os artefatos.'
