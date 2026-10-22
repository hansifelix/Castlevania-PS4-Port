# Etapa 21 — Recompilação AArch64 real, em programa sintético

Esta etapa **não** faz o port de Castlevania e não executa o jogo. O objetivo é testar um elo novo no pipeline:

1. Montamos a representação binária AArch64 de `mov w0,#42; add w0,w0,#1; ret` (3 instruções próprias, verificadas com Clang/llvm-objdump).
2. O **analisador e emissor do recompilador público** `BelmanteGu/SuperMarioWonderRecomp`, commit `010ed7a596a621c15d3a8dfa5795ca8c3668b066`, geram C++ a partir desses bytes. Não usamos tradução manual para o C++.
3. O programa C++ gerado roda em um runner Linux x86-64 e deve devolver o valor **43** via `nx::CPU`. Isso é um teste de comportamento limitado.
4. O OpenOrbis compila e liga o mesmo C++ gerado como um ELF x86-64 alvo PS4 **sem instalá-lo no console**. Usa adaptação **temporária** do header `nx/cpu.h`, já necessária na Etapa 20.

Não há NSO, NSP, RomFS, código ou assets comerciais. Nenhum dado privado ou derivado de jogo é enviado para GitHub. Nenhum `eboot.bin`/PKG é gerado.

### Critérios de aprovação
- Exatamente 3 instruções ARM64 aceitas pelo emissor, nenhuma não suportada.
- Saída em C++ com 1 função.
- Teste Linux retorna 43.
- ELF PS4 `ELF64` e máquina `X86-64`, link sem símbolos pendentes.

**Isso não comprova compatibilidade do carregador de módulos reais, reservas de endereço, APIs de sistema, gráficos NVN nem execução do menu de Castlevania.** Próximas investigações devem priorizar esses bloqueios em vez de gerar PKGs de demonstração.
