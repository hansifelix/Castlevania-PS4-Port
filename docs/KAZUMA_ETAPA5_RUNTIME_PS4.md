# Kazuma Port Games BR — Etapa 5: compilação cruzada de fontes do runtime para PS4

## Objetivo verificável

Usar o compilador Clang com alvo `x86_64-pc-freebsd12-elf` e os headers do **OpenOrbis SDK v0.5.4** para produzir **objetos ELF relocáveis** (`.o`) de quatro unidades de código **originais e públicos** do projeto [SwonDev/cstlvnia-blmont-to-macos](https://github.com/SwonDev/cstlvnia-blmont-to-macos), usando a revisão fixa `4043f21bb4f656d34cd17ba070238c7728d00631`.

São verificadas, individualmente, estas fontes:

1. `games/castlevania/game.cpp`: perfil público de Castlevania, não o conteúdo do jogo.
2. `runtime/src/nvn/nvn_gpu_pick.cpp`: seleção de GPU em modo `NX_GPU_PICK_STANDALONE`, **não** Vulkan real.
3. `runtime/src/kernel_thread_control.cpp`: rotinas do runtime para controle de threads.
4. `runtime/src/svc_info.cpp`: serviço de informações (`svcGetInfo`) do runtime.

A pipeline **FALHA** se algum dos quatro arquivos não compilar ou não produzir ELF relocável `EM_X86_64`. O comando usa `set -euo pipefail`, e grava relatórios, incluindo falhas, em `kazuma-etapa5-compilacao-real-ps4-sem-jogo`.

## O que NÃO valida

- Não há integração dos objetos em um único executável, carregamento de runtime, `eboot.bin`, nem `PKG`.
- Não se prova que o código relocado funciona no PS4 ou que símbolos externos podem ser resolvidos. Há várias dependências de runtime pendentes.
- Não são compilados módulos comerciais `main`, `sdk` ou `subsdk0`. Nenhum NSP, NCA, APK, ROM, chave, recurso ou mídia proprietária é utilizado ou enviado.
- Não comprova áudio, Vulkan/RADV, saves, jogabilidade, inicialização, estabilidade nem desempenho no console.
- Um check verde aqui prova **apenas** compilação estática dos quatro arquivos-alvo com o toolchain usado. A v1.3.2 de vídeo que abriu no console e as versões posteriores que falharam continuam sendo um problema separado, a investigar antes de qualquer instalação.

## Reprodutibilidade e segurança

Fonte pinada pelo SHA completo; OpenOrbis LLVM 18 (`v0.5.4`) por URL de release e SHA256 já usado pelos workflows anteriores do projeto. Artifacts contêm **relatórios e objetos de fontes públicas**, não dados do jogo. Esta PR não altera as capas e assinaturas Kazuma Port Games BR.

## Depois deste teste

Verificar quais funções de `nx::plat` e quais símbolos desses objetos precisam de implementações PS4. Somente planejar ligação/empacotamento quando houver evidência de compatibilidade; evitar instalar testes no PS4 até investigar as repetidas verificações de armazenamento após desligamentos e fazer backup de saves.
