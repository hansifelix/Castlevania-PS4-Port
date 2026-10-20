# Kazuma Port Games — Runtime etapa 1: ponte Npad verificável (sem jogo)

## Referências verificadas (20/10/2026)

- [Castlevania para macOS, `runtime/src/platform.h`](https://github.com/SwonDev/cstlvnia-blmont-to-macos/blob/main/runtime/src/platform.h): `nx::plat::PadState` tem `uint64_t buttons` e quatro eixos `int32_t`; os bits são **A=0, B=1, X=2, Y=3, StickL=4, StickR=5, L=6, R=7, ZL=8, ZR=9, Plus=10, Minus=11, Left=12, Up=13, Right=14, Down=15**.
- [Implementação Linux, `platform_linux.cpp`](https://github.com/SwonDev/cstlvnia-blmont-to-macos/blob/main/runtime/src/platform_linux.cpp): Y positivo significa **para cima**, e valores absolutos inferiores a 7849 são ignorados.
- O adaptador local `src/input_adapter.*` gera uma máscara simplificada de 32 bits com posições diferentes. Ela **não deve** ser usada diretamente como o campo de botões do runtime acima.
- [PS4 SMW, `port/ps4_runtime.cpp`](https://github.com/iHaiDeeZ/SMW/blob/main/port/ps4_runtime.cpp): referência de port de *outro* jogo, não um runtime de Castlevania pronto para uso.

## O que foi implementado

`src/runtime_bridge/npad_bridge.*` converte a máscara de botões do nosso protótipo de DualShock 4 em **valores Npad do runtime público**, incluindo limites e zona morta dos analógicos já normalizados. O teste `tests/test_npad_bridge.cpp` valida cada botão, os dois esquemas Cross/Circle, combinações e limites dos eixos.

**Limites críticos:** isto roda somente em Linux/host e não foi ligado a `scePad`, `nx::plat::read_pad`, ao código do jogo, a um `eboot.bin` ou a Vulkan/RADV. Não lê valores brutos do DualShock 4: a futura integração no PS4 deverá ler/normalizar os valores de `scePad` e confirmar os sentidos dos eixos e triggers.

Para testar sem SDK do PS4, `cmake -S . -B build && cmake --build build && ctest --test-dir build --output-on-failure`.

## Próximos bloqueios reais (sem testes no console ainda)

| Subsistema requerido por `nx::plat` | Evidência atual | Próximo critério |
| --- | --- | --- |
| Entrada / Npad | Ponte numérica testada no host | Ler `scePad` em runtime PS4 e integrar `read_pad` |
| Memória e VA fixo | Probe anterior de alocação básica, **não** de mapa convidado | Planejar reserva/commit/decommit no PS4 sem colisões |
| Clock e threads | Ainda sem implementação ligada a runtime real | Validar monotonicidade e contratos de threading |
| Sistema de arquivos | Sem integração de RomFS/save | Definir caminhos separados: somente leitura vs gravável |
| Áudio | Sem ponte `sceAudioOut` | Medir formato PCM, fila e callback |
| Vídeo | VideoOut anterior exibiu imagem; Vulkan/RADV falhou em PKGs experimentais | Diagnosticar eboot/PKG, depois WSI Vulkan/RADV |
| Recompilação AArch64 → C++ | Ferramentas públicas identificadas, **sem execução do jogo** | Verificar versão/build IDs com arquivos obtidos licitamente; somente depois tentar build x86-64 |

## Segurança

Não há chaves, jogos, ROMs, NSP, imagens oficiais nem arte proprietária neste PR. Ele não produz pacote instalável. Com verificações de armazenamento do PS4 em desligamentos, manter o console fora dos testes experimentais até avaliar sua estabilidade e preservar saves.
