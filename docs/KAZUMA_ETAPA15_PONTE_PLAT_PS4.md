# Kazuma Etapa 15 - Subconjunto PS4 da plataforma nx::plat

Esta etapa implementa as funcoes publicamente declaradas em `runtime/src/platform.h` do projeto SwonDev/cstlvnia-blmont-to-macos (commit `4043f21bb4f656d34cd17ba070238c7728d00631`):

- `nx::plat::read_pad(PadState&)` por `scePadReadState` do OpenOrbis/PS4. Interface recebe handle criado pelo Test 04; traduz posicoes fisicas de DualShock 4 para layout do Switch. NAO inclui rumble, touch ou todos os controles.
- `nx::plat::monotonic_ns()` pela funcao `sceKernelGetProcessTime()` do OpenOrbis (microsegundos convertidos em nanosegundos); validacao empirica de crescimento no PS4 fica pendente.

As duas funcoes estao em `tools/etapa15/plat_ps4.cpp` e sao usadas pelo homebrew Test 04 sem arquivos comerciais. Ele conserva codigo e dependencias do Test 03, inclusive a prova de selecao *simulada* de GPU, e acrescenta:

- `NX PLAT TEMPO: OK` somente se o relogio devolve valores crescentes ao longo dos frames.
- `NX PLAT INPUT: OK` apos apertar X e a ponte mapear o botao para `nx::plat::kB` (posicao inferior Nintendo).
- Botao Circulo solicita sair via SystemService, como Test 02/03; usar botao PS para fechar se houver falha.

O Title ID sera `BREW91237`; nao instala nem substitui outros Testes. Primeiro conferir compilacao, ligacao, manifestos e logs; o teste real no console e opcional e devera ser feito somente apos os checks.

**Limites:** nenhuma implementacao de `nx::plat::reserve`, `commit`, `decommit`, `create_window`, Vulkan, audio, threads, carregador, memoria guest fixa, execucao AArch64 ou menu de Castlevania. Nem `NX PLAT INPUT: OK` nem `NX PLAT TEMPO: OK` provam portabilidade do jogo completo. Nunca enviar arquivos de jogo ou chaves ao repo publico.
