# Kazuma Port Games BR — Etapa 18: auditoria do mapa de memória

## Contexto

A Etapa 17 (`Test 06`) demonstrou um mapeamento dinâmico **de 64 KiB dentro do processo homebrew**, com endereço escolhido pelo sistema operacional. Isso não é equivalente às regiões de memória guest que o runtime público do projeto de referência exige.

## Escopo da etapa

A CI consulta os **cabeçalhos públicos** `runtime/include/nx/runtime.h` e `runtime/include/nx/cpu.h` do repositório `SwonDev/cstlvnia-blmont-to-macos` no commit fixado `4043f21bb4f656d34cd17ba070238c7728d00631`.

O auditor extrai constantes de faixa, analisa sobreposições matemáticas e gera relatórios para as configurações *Linux, Android e macOS* da origem. O PS4 não consta entre esses alvos originais, portanto **não** declaramos nenhum endereço seguro para uso no PS4.

## O que deve sair do GitHub Actions

- `AUDITORIA_MAPA.md` com comparativo do mapa nominal.
- `mapa_linux.json`, `mapa_android.json` e `mapa_macos.json` com intervalos `[inicio, fim)` e achados.
- Testes Python locais de parsing, sobreposição e limites.

**Não será produzido PKG.** **Não haverá teste no console.** **Não reservar endereços fixos com `MAP_FIXED` nem modificar kernel ou firmware.** Os arquivos são apenas relatórios. Não há arquivos comerciais do jogo.

## Questões abertas

1. O espaço de endereço de um processo homebrew PS4 permitiria reproduzir o mapa guest? Não verificado.
2. A camada `nx::plat::reserve`, `commit`, `decommit` pode ser implementada adequadamente? Não implementada.
3. As restrições de memória, carregamento do código recompilado e renderização NVN viabilizam o port? Ainda desconhecido.

A auditoria não é evidência de progresso direto rumo ao menu original de Castlevania, mas ajuda a identificar obstáculos antes de implementar código com riscos de instabilidade.
