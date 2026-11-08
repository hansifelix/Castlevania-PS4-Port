# Castlevania PS4 — callback de material de carregamento

A camada `src/ps4/castlevania_loading_material.cpp` adapta a
implementação pública MIT de `games/castlevania/loading_animation.cpp`
do upstream fixado `4043f21bb4f656d34cd17ba070238c7728d00631`,
antes compilada somente para macOS (`__APPLE__`).

O hook real `nx_castlevania_loading_material(nx::CPU&, void(*)(nx::CPU&))`
preserva a ordem das chamadas dos endereços guest de revisão fixada:
ler material em `self + 0x38 -> settings + 0x18`; obter índice atual via
`nx::call(NX_BASE+0x1dcc470)`; preparar o material via
`nx::call(NX_BASE+0x4e1aba0)`; **só então** executar a função original.
Sem material, somente a função original é chamada. Sem original, falha
explicitamente, nunca mascara o erro.

CTest utiliza CPU, memória e `nx::call` sintéticos sem nenhum dado de jogo.
A workflow de ABI usa OpenOrbis v0.5.4 Clang 18 e headers REAIS do upstream,
sem publicar objetos AOT nem ROMs. O linker privado deve confirmar que o
hook deixa de estar indefinido e que os símbolos externos não são escondidos.

Não entrega `eboot.bin`, PKG ou renderização real PS4. A implementação
da animação de carregamento não substitui o backend NVN, nem valida boot.
