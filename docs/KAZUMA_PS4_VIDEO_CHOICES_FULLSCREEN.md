# PS4: callbacks reais de seleção de vídeo e modo tela cheia

Portados do arquivo MIT público `games/castlevania/video_options.cpp`,
rev `4043f21bb4f656d34cd17ba070238c7728d00631`.

Três símbolos do AOT: `nx_castlevania_supported_resolutions`,
`nx_castlevania_fullscreen_mode` e `nx_castlevania_fullscreen`.

A rotina de resoluções aguarda a função original popular os arrays gerenciados.
Lê a tabela e os objetos verdadeiros do jogo, valida limites/índices e marca
ativadas apenas resoluções 16:9 até o VideoOut nativo (com remoção de repetidas).
Seleciona a resolução interna atualmente configurada e usa a chamada guest
`System.String.FastAllocateString` para o rótulo nativo, reutilizando strings.
No PS4 o único modo de janela válido é fullscreen (modo 1); não há desktop.

Testes host com CPU, strings e arrays sintéticos verificam os contratos.
Cross-compilação PS4 com upstream `nx/runtime.h` pinado e OpenOrbis v0.5.4
liga os provedores reais de resolução usando `ld.lld -r`.

**Limites:** a linkagem host/PS4 parcial sem código comercial não é um boot.
As rotinas `video_initialize` e `set_fullscreen_mode` ainda precisam ser
adaptadas; serviços gráficos NVN, instruções SVE/STG, linker estrito e
`eboot/PKG` do jogo permanecem pendentes. Sem publicar arquivos proprietários.
