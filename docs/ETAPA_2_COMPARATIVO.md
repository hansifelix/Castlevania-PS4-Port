# Etapa 2 — Análise do código publicamente disponível (19/10/2026)

**Documento de engenharia: nenhum código do jogo foi compilado para PS4.**

## Bases de código verificadas (repositórios públicos)

1. Castlevania: https://github.com/SwonDev/cstlvnia-blmont-to-macos
   - `games/castlevania/build.json`: `content_version = "1.1.0"`; referência explícita a 3 módulos (`main`, `sdk`, `subsdk0`) e a hashes/build IDs específicos da revisão.
   - `games/castlevania/modules.cmake`: `set(NX_MODULES main sdk subsdk0)`.
   - `games/castlevania/game.cpp`: identidade `0x0100BA4026E94000`; instalação de políticas de filme/resolução condicionada a `__APPLE__`.
   - `recomp/emit.py`: traduz instruções AArch64 em funções C++ que recebem contexto `nx::CPU`; o código gerado NÃO é publicado junto do jogo e deve ser produzido localmente com material autorizado.
   - `runtime/src/platform_mac.cpp`, `runtime/src/mac_video.mm`, `runtime/src/mac_memory.cpp` e `runtime/src/nvn/`: implementação macOS com dependências de SDL/AppKit/Metal por MoltenVK/Vulkan, memória e NVN. Não pode ser simplesmente recompilada como está para PS4.
   - CMake usa Clang e pode compilar testes sem dumps (`NX_BUILD_GAME=OFF`). Isso NÃO valida jogabilidade.

2. PS4: https://github.com/iHaiDeeZ/SMW
   - `docs/BUILDING.md`: toolchain OpenOrbis/PacBrew e Clang/LLVM 21, Mesa RADV, target x86-64 Jaguar (`-march=btver2`), recompilação estática AArch64→C++ e pacote PKG.
   - `patches/wonder-ps4.patch`: alterações próprias do jogo **Mario**, não aplicáveis diretamente ao Castlevania.
   - `port/ps4_runtime.cpp`, `port/mesa*`, `toolchain/`: componentes específicos da plataforma, candidatos a estudo/adaptação. Uso exige respeitar licenças, interações ABI e dependências.
   - `runtime/src/platform_ps4.cpp` e `runtime/src/ps4/ps4_vk_wsi.cpp` existem como alterações produzidas pelo projeto SMW em sua base de upstream, não necessariamente como arquivos independentes no checkout raiz do projeto SMW.

## Resultado da verificação feita no Termux pelo usuário

`Castlevania.zip`: 6 entradas; PFS0 base + update + DLC legíveis, com limites coerentes.

| Nomeado como | Title ID | versão interna | bytes informados | estrutura |
| --- | --- | --- | ---: | --- |
| Base | 0100BA4026E94000 | 0 | 560321310 | 7 entradas PFS0 OK |
| Atualização | 0100BA4026E94800 | 65536 | 3182299415 | 7 entradas PFS0 OK |
| DLC | 0100BA4026E95001 | 0 | 106128 | 2 entradas PFS0 OK |

O título base de Castlevania corresponde à identidade em `game.cpp`.
A atualização rotulada 1.1.0 coincide com a revisão que o projeto Mac espera.
**Não foi verificado hash/build ID do código NSO**, porque a auditoria não decripta
NSPs, nem inspeciona o conteúdo NCA. Portanto não podemos afirmar que os
arquivos satisfazem os hashes em `build.json`.

## Lacunas técnicas reais

### 1. Recompilador + identificação do jogo
- Reutilizar a arquitetura Python AArch64→C++ do projeto Mac, não as bibliotecas `.so` ARM64 do Android.
- Confirmar a mesma revisão efetiva de cada módulo via identificadores/hashes autorizados; não confundir o Title ID do pacote com o Build ID de cada módulo.
- Verificar se os módulos em C++ são portáveis para Clang x86-64 (`main`, `sdk`, `subsdk0`), com ABI, endianness, intrínsecos e tratamento de exceções corretos.

### 2. Runtime do PS4
- Compatibilizar inicialização, carregamento de módulos, mapa de memória do convidado e exceções/sinais.
- Substituir inicialização de vídeo Mac/SDL/AppKit por saída PS4 e NVN → Vulkan/RADV (incluindo texturas ASTC e shaders).
- Implementar áudio em `sceAudioOut`, pad em `scePad`, filesystem e salvamentos, relógio e threads.
- Revistar cenas/vídeos/cutscenes e interface específica de Castlevania; não assumir que os patches de Mario resolvem.

### 3. Ambiente de compilação
- Requer SDK e toolchain compatíveis com OpenOrbis e um host com recursos (PC ou host cloud com suporte à toolchain); Termux serve para análises preliminares.
- Antes de processar dados de jogo, primeiro **compilar e instalar um PKG de teste independente**, com vídeo e um botão de DualShock, e colher log ou captura para comprovar.

## Marcos de aceitação (somente avançar com evidência)

- [x] Arquivos com formato e Title IDs esperados (análise de contêiner, não integridade total).
- [x] Referência pública de recompilador **específico** de Castlevania 1.1.0 identificada.
- [x] Referência pública de runtime de PS4 x86-64 identificada.
- [ ] Ambiente de compilação PS4 real configurado e testado.
- [ ] PKG homebrew **sem jogo** gera `eboot.bin`, instala e inicia no PS4 Slim.
- [ ] Módulos de Castlevania recompilados para x86-64 sem bloqueios de compilação.
- [ ] Runtime PS4 exibe pelo menos primeiro quadro do jogo.
- [ ] Controle, áudio, salvamentos, estabilidade e desempenho validados.
- [ ] PKG final com arte personalizada gerado **apenas para uso autorizado**.

**Evitar falsas conclusões:** arte pronta, testes unitários C++ e auditoria PFS0 não implicam que Castlevania seja jogável no PS4. O projeto PS4 de Mario prova viabilidade para outro jogo, não disponibilidade de um conversor universal.
