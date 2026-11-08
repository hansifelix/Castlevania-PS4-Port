# Castlevania PS4 — video defaults reais (PR seguinte à #105)

Origem MIT fixada: `games/castlevania/video_options.cpp` do upstream
`4043f21bb4f656d34cd17ba070238c7728d00631`.

`nx_castlevania_video_defaults(nx::CPU&, void(*)(nx::CPU&))` invoca primeiro
a função original do jogo. Depois lê os campos estáticos existentes, preserva
as listas que não têm exatamente 12 entradas, e escreve somente o último par
(resolução nativa) das listas geral e 16:9. O tamanho nativo vem da ponte
PS4 `configure_native`, previamente alimentada por `sceVideoOutGetResolutionStatus`.
Sem VideoOut válido e com listas presentes, falha explicitamente: não inventa 1080p.
Sem metadados do jogo, não escreve em endereços arbitrários.

O teste host usa memória sintética, com remapeamento exclusivo da leitura
`NX_BASE+0x6be3ec8`. A compilação ABI no CI usa `nx/runtime.h` real upstream,
OpenOrbis v0.5.4 e Clang 18, sem esses testes sintéticos, sem ROM e sem código
proprietário.

**Limites**: nenhum PKG/eboot, nenhuma prova de gameplay. O linker AOT privado
ainda deverá demonstrar a resolução do símbolo e a ligação executável final.
A conversão SVE/STG e o backend gráfico permanecem pendentes.
