# Castlevania PS4 — VideoOut conectado ao ponto real de inicialização

## Implementação

`src/ps4/castlevania_game_ps4.cpp` implementa o contrato público
`nx::game::kInfo/after_init/renderer_start/first_frame` com os metadados da
revisão upstream fixada (MIT). **Substitui** o `games/castlevania/game.cpp`
upstream em um futuro build PS4: nunca compilar os dois juntos.

O `nx::boot()` upstream chama `nx::game::after_init()` após os construtores dos
módulos e **antes** de `nnMain`. A implementação PS4 consulta
`nx::plat::screen_size()`, cujo provedor PS4 existente em
`tools/etapa74/platform_ps4_display.cpp` obtém as dimensões via
`sceVideoOutGetResolutionStatus`. Só com dados válidos e 16:9 chama
`kazuma::ps4::video::configure_native` (PR #101). Sem VideoOut, com erro de
consulta ou tamanho incompatível, chama `nx::fatal` e impede o início.

`renderer_start` e `first_frame` não possuem adaptação de renderização PS4:
permanecem vazios exatamente como no upstream; NÃO são um backend NVN.

## Verificação reproduzível

O CTest `test_ps4_castlevania_boot_gate` liga **os arquivos reais de projeto**
`castlevania_game_ps4.cpp` e `castlevania_resolution.cpp` usando apenas
interfaces sintéticas para simular o VideoOut e CPU no host, com casos de
ausência, resolução inválida, 1080p, transição para 720p e metadados.

A compilação PS4 OpenOrbis/Clang 18 do provider de game é checada pela workflow
`kazuma-ps4-game-videoout-abi.yml` usando as interfaces REAIS de
`nx/game.h` e `platform.h` no upstream MIT fixado.

Limitações: não existe `eboot.bin` do jogo, PKG, link executável estrito,
renderização Vulkan/NVN PS4 integrada nem validação de boot no hardware. A
ligação real desta entrada com os módulos AOT e runtime completo permanece
uma etapa de integração privada; não publicar objetos ou código do jogo.
