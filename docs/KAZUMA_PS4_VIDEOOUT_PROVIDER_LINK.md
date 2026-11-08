# Castlevania PS4 — VideoOut provider ligado ao game hook (Etapa seguinte)

A PR #102 adicionou `nx::game::after_init()`, que solicita
`nx::plat::screen_size()` antes de `nnMain`. O código real do provedor
já existia em `tools/etapa74/platform_ps4_display.cpp` e usa
`sceVideoOutOpen`, `sceVideoOutGetResolutionStatus`, `sceVideoOutClose`.

O novo CI compila os **dois providers reais** com OpenOrbis v0.5.4
(Clang 18), usando o upstream MIT fixado em
`4043f21bb4f656d34cd17ba070238c7728d00631`. Executa
`ld.lld-18 -m elf_x86_64 -r` e comprova que o símbolo
`nx::plat::screen_size` está definido, **não** consta entre os
indefinidos, enquanto as chamadas reais do SceVideoOut continuam como
dependências externas explícitas a serem resolvidas com biblioteca SDK
em link executável estrito.

O CI não recebe nenhum arquivo de jogo. **Não** é um eboot.bin,
nem um PKG, nem teste de boot. O passo seguinte é adicionar ambos ao
link privado dos 1.916 objetos AOT e resolver chamadas a libSceVideoOut,
demais callbacks de vídeo, serviços runtime, NVN/Vulkan, STG e MOV SVE.
