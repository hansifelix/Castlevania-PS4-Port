# Marco 5 — Ponte DS4/Npad e link com perfil real de Castlevania

Objetivo: compilar a ponte de entrada que satisfaz o contrato `nx::plat::read_pad` do runtime público, testar a conversão com dados sintéticos no Linux e fazer link de um `eboot.bin` com `games/castlevania/game.cpp` e controle PS4 nativo.

Isso **não** inicia o jogo: o AOT (main/sdk/subsdk0), renderer NVN→Vulkan, serviços do Horizon, shaders e recursos ainda **não** foram integrados. O binário é um diagnóstico sem interface de vídeo. A imagem do PKG v0.8 fica intacta; não instale um novo PKG nesta etapa.

O pipeline obtém upstream `SwonDev/cstlvnia-blmont-to-macos` pela revisão fixa `4043f21bb4f656d34cd17ba070238c7728d00631`, usa o compilador OpenOrbis v0.5.4, inclui o perfil de Castlevania e converte os dados do DualShock 4 à estrutura de controle utilizada pelo jogo, preservando as posições físicas A/B/X/Y.

**Como saber que avançamos:** o workflow gera `castlevania-controle-eboot-test` e os testes Linux de conversão passam. Um eboot compilado não garante inicialização em hardware. Próxima frente: camada de memória PS4 (`reserve/commit`) e, depois, saída Vulkan com RADV para tela. O código do jogo e recursos comerciais devem permanecer fora do GitHub.

Não há necessidade de inserir NSP, APK ou chaves no CI. O conteúdo 1.1.0 compatível ainda será necessário em um estágio posterior e deve vir de uma cópia obtida legitimamente.
