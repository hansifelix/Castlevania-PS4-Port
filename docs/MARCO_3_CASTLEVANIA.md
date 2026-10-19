# Marco 3: primeiro teste do código específico de Castlevania no alvo PS4

**Ainda NÃO é jogo jogável. Não cria APK, PKG nem eboot Castlevania.**

## O que este teste valida

- Clona o código-fonte aberto do port de macOS em revisão fixa `4043f21bb4f656d34cd17ba070238c7728d00631`.
- Compila e executa os contratos básicos de escolha de GPU, bindings, quads e interface de controle desse runtime no Linux.
- Compila `games/castlevania/game.cpp` do projeto de código aberto como objeto ELF **x86-64 para o alvo FreeBSD/PS4**, usando OpenOrbis.
- Publica **somente** `game.o` de perfil (metadados e funções vazias). Não há gameplay ou recursos do jogo.

## Bloqueios antes da primeira cena de Castlevania

1. Verificar, **localmente**, o ExeFS 1.1.0 (`main`, `sdk`, `subsdk0`) por hash/build ID, sem enviar material proprietário a repositorios públicos.
2. Gerar código C++ do jogo com recompiler AArch64->C++ e compilá-lo para x86-64; esse código gerado não é publicado no repositório.
3. Adaptar ao PS4 os serviços de plataforma do runtime: memória virtual guest, threads, exceções e arquivos, Pad e `sceAudioOut`.
4. Levar NVN->Vulkan a Mesa RADV do PS4, apresentar vídeo pelo VideoOut, lidar com shaders, formatos e sincronização.
5. Só depois criar PKG funcional e testar abertura, carregamento, primeira cena e FPS no PS4 Slim.

## Referências

- https://github.com/SwonDev/cstlvnia-blmont-to-macos (base MIT, conteúdo 1.1.0)
- https://github.com/iHaiDeeZ/SMW (arquitetura ilustrativa de port x86-64/PS4 para OUTRO jogo)
- https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain

## Limites

Testes de host e compilação de `game.cpp` não demonstram que o runtime inteiro é compatível com PS4, nem avaliam FPS. **Não copie NSP/XCI, chaves, código comercial recompilado, shaders ou dados proprietários ao GitHub.**
