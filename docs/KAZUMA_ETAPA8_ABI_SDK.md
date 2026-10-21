# Kazuma Port Games BR — Etapa 8: ABI, simbolos e bibliotecas do OpenOrbis

## Motivo
A etapa 7 compilou 7 objetos originais de fontes publicas. O relatorio anterior indicou que 7 das 34 referencias da etapa 6 sao providas por `kernel.cpp`, `memory.cpp` e `loader.cpp`. Ao adicionar esses arquivos podem surgir **novas referencias**. Nao podemos concluir que sobraram apenas 27 referencias totais.

## Experimento reproduzivel
- Recompilar as 4 unidades de fonte originais usadas na etapa 5, com alvo `x86_64-pc-freebsd12-elf`.
- Recompilar `kernel.cpp`, `memory.cpp` e `loader.cpp` usados na etapa 7, preservando os objetos temporarios da CI.
- Reunir os 7 objetos como **ET_REL** usando `ld.lld -r` (nao um executavel).
- Comparar o conjunto de simbolos indefinidos antes/depois, incluindo novas referencias introduzidas pelos provedores.
- Procurar os simbolos indefinidos exportados em arquivos `.a` de `OpenOrbis/PS4Toolchain/lib`; encontrar nome coincidente e apenas pista para possivel futura ligacao, nao prova de que o link final funcionara.
- Guardar `resumo.json` e logs como artefato do GitHub; **nunca publicar objetos binarios comerciais**.

## Interpretacao dos resultados
- Checks verdes: apenas auditoria offline concluida. A existencia de arquivos `.a` com simbolos correspondentes nao garante ABI, versao de biblioteca, link final, estabilidade, carregamento no PS4 ou jogo executavel.
- Novo passo futuro: identificar interfaces faltantes de plataforma e **prototipar um executavel homebrew minimo independente**, sem usar arquivos do jogo, antes de qualquer tentativa de PKG.
- Nenhum NSP/APK/NCA/ROM, modulo comercial, eboot, PKG ou instalacao no console nesta etapa.
