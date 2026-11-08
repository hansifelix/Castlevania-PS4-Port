# Castlevania PS4: inicialização de vídeo e modo de tela cheia

Dois callbacks adicionais do upstream MIT fixado na revisão
`4043f21bb4f656d34cd17ba070238c7728d00631`:

- `nx_castlevania_video_initialize`: executa a rotina original do jogo,
  reutiliza o **mesmo** provider de listas gerenciadas da PR #109 e
  valida as opções usando os getters e validadores originais da classe.
  Para evitar retorno recursivo, mantém uma guarda `thread_local`.
- `nx_castlevania_set_fullscreen_mode`: no PS4 normaliza a escolha do
  jogador para fullscreen nativo (modo 1) e chama a função original
  para atualizar o estado do jogo. Não usa janela de macOS/PC.

O teste host usa arrays sintéticos, estruturas gerenciadas e dispatcher guest
simulado: verifica ordem, seleção, validação da resolução e janela,
recursão durante inicialização, falhas explícitas e restauração da guarda.

Compilação ABI no CI com headers reais `nx/runtime.h` e OpenOrbis/Clang 18
liga ambos os callbacks com `castlevania_video_choices_ps4.cpp` e
`castlevania_resolution.cpp` em objeto relocável e audita definições.

**Ainda não há** eboot/PKG, render NVN ou prova de boot no hardware.
Não publicar ROM/objetos comerciais; o link com 1.916 objetos AOT privados
é etapa posterior.
