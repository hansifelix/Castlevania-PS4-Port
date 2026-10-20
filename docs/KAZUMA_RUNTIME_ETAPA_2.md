# Kazuma Port Games — Runtime etapa 2: planejamento de memoria convidada

Esta etapa adiciona um **planejador de intervalos de enderecos** com verificacao de alinhamento, overflow, sobreposicoes e insercao ordenada. Os testes sao executados em Linux/Termux sem nenhum arquivo comercial do jogo.

## Por que isso importa

O runtime publico de Castlevania (macOS) declara `nx::plat::reserve`, `commit` e `decommit`, cujo proposito e disponibilizar memoria do programa convidado em enderecos precisos. O PS4 exige uma implementacao propria dessas operacoes. Nosso planejamento permite verificar intervalos antes de fazer chamadas potencialmente perigosas ao sistema.

Referencias verificadas:
- https://github.com/SwonDev/cstlvnia-blmont-to-macos/blob/main/runtime/src/platform.h
- https://github.com/SwonDev/cstlvnia-blmont-to-macos/blob/main/runtime/src/platform_linux.cpp
- https://github.com/iHaiDeeZ/SMW/blob/main/port/ps4_runtime.cpp

## Resultado real desta etapa

`src/runtime_bridge/guest_memory_plan.hpp/.cpp`: valida intervalos semiabertos `[inicio, fim)`, tamanho de pagina configuravel (potencia de dois), multiplos da pagina, overflow de `uint64_t`, contiguidade permitida e sobreposicao proibida. Erros nao alteram o plano.

`tests/test_guest_memory_plan.cpp`: testes em modo Release com verificacoes que nao dependem de `assert()`.

## Nao foi feito

- **NAO** reserva, mapeia ou libera memoria real do PS4 (nenhum `sceKernel...`).
- **NAO** integra `nx::plat::reserve/commit/decommit` ao runtime.
- **NAO** gera `eboot.bin`, PKG, executavel do jogo ou dados de jogo.
- **NAO** determina o mapa real do processo convidado nem prova que seu PS4 consegue reserva-lo.
- **NAO** resolve Vulkan, inicializacao de executaveis ou integridade do armazenamento do PS4.

Os testes usam 0x4000 como pagina de exemplo, **nao** como afirmação definitiva sobre a granularidade necessaria no PS4. Um futuro adaptador deve consultar as APIs e requisitos reais antes de tocar em enderecos reais.

## Proximos marcos

1. Consolidar os contratos de memoria e verificar os enderecos efetivamente exigidos pelo runtime.
2. Validar restricoes do ambiente de PS4 e suporte a reserva fixa, sem escrever PKG ate que o console esteja estavel.
3. Ligar o planejador a um adaptador PS4 com tratamento de falhas e logs, inicialmente em testes mockados.
4. Abordar threads/tempo, filesystem e audio em etapas isoladas e auditaveis.

Nenhuma chave, NSP, NCA, ROM, jogo, imagem proprietaria ou dump deve ser colocado em repositorio publico.
