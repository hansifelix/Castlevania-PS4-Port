# Kazuma Port Games BR — Etapa 26: teste de link Vulkan para PS4

## Meta verificavel

Compilar o exemplo **publico** de triangulo do `orbis-porting-kit` com o SDK+overlay+Mesa/RADV precompilado emparelhados na release `orbis-sdk-v1`; confirmar um ELF64 x86-64 e `eboot.bin` no **runner do GitHub**. Capturar erros de configuracao/compilacao/link no workflow. Nao cria PKG, nao altera PS4.

## Fontes

- `orbis-ports/orbis-porting-kit` commit `213b0c38ff25ea7ca402c8844a6494086d0f1cae`.
- `orbis-ports/orbis-porting-kit` release `orbis-sdk-v1` (release verificada pelo action `setup-orbis`).
- O bundle contem OpenOrbis, `orbis-compat` e Mesa PS4 prontos/pareados; nesta etapa **nao recompilamos RADV**. A versao em hardware segue desconhecida ate consulta real no PS4.

## Gate e riscos

- Build e link do **exemplo** nao validam a implementacao Vulkan no console.
- Nao e o jogo, nao utiliza seus assets e nao testa NVN, carregador, memoria fixa ou scripts de recompilacao do Castlevania.
- Nao publica `eboot.bin` instalavel e nao gera PKG. Relatorios guardam os hashes e dados tecnicos.
- Validar checks e ler `relatorios/etapa26` antes do merge.
- Apenas apos link confiavel, planejar o primeiro teste grafico minimo em hardware, respeitando o travamento que ja ocorreu no PS4.
