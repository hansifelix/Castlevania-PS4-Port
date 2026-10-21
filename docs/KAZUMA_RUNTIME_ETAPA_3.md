# Kazuma Port Games — Runtime, etapa 3: relogio e sincronizacao (HOST-ONLY)

## Finalidade

Criar blocos C++17 com testes reais de concorrencia e tempo antes de tentar implementar os contratos `nx::plat::monotonic_ns`, `sleep_ns`, `yield` e `start_thread` num PS4. Base publica consultada: https://github.com/SwonDev/cstlvnia-blmont-to-macos/blob/main/runtime/src/platform.h .

## Entrega

- `MonotonicFloor`: garante que observacoes sucessivas nao recuem, inclusive sob atualizacoes concorrentes.
- `milliseconds_to_ns_saturated`: conversao com protecao de overflow.
- `host_steady_clock_ns`: relogio do host apenas para comparacao e testes, nao e a API do PS4.
- `OneShotSignal`: evento persistente com `condition_variable` e predicado, para testar sincronizacao e ausencia de perda de sinais.
- `tests/test_time_thread_contract.cpp`: valida regressao do tempo, saturacao, timeout zero, duas threads esperando e quatro threads atualizando o relogio. CHECK funciona em Release.

## Limites importantes

Nenhuma implementacao `nx::plat` real, nenhum `sceKernel`, nenhuma reserva de memoria do PS4, nenhuma API de clock/threads PS4, nem tentativa de compilar Castlevania. Esta e uma etapa de **contratos em ambiente Linux/Android Termux**. Testes verdes nao medem desempenho, compatibilidade grafica, jogabilidade, armazenamento ou estabilidade do console.

## Proximas verificacoes para realmente aproximar do jogo

1. Identificar implementacao e assinaturas exatas de relogio e sincronizacao no ambiente OpenOrbis; revisar resolucao/epoca/unidades com documentacao e experiencia comprovada.
2. Criar adaptador para o runtime `nx::plat` com tratamento de erro/sem side effects indesejados, testado por mocks; so integrar ao PS4 quando ele estiver estavel.
3. Reservas fixas de memoria: verificar mapa convidado exigido pelo jogo (a etapa 2 apenas valida intervalos).
4. Compilar partes portaveis do runtime no cross-compiler e resolver dependencias, sem material comercial publicado.
5. Auditar `eboot.bin` e PKG que falharam antes de qualquer nova instalacao; testes no PS4 somente depois de esclarecer desligamentos incorretos e salvar dados.

## Testar no projeto

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 2
ctest --test-dir build --output-on-failure
```

Nada neste PR deve conter NSP, NCA, chaves, APK, ROM, dumps, arquivos comerciais ou a capa personalizada.
