# Kazuma Port Games BR — Etapa 47 — Diagnóstico de temporização NATIVA no PS4 (sem jogo)

## Evidência que motivou a correção
Etapa 46: `sleep_ns(2_000_000)` apresentou `DELTA_NS=1000` a `22000` nos logs. Isso é menor que o solicitado. Os valores 63,5–63,8 FPS de 46 são provisórios, e não medem Castlevania.

## Alteração (escopo limitado)
- Novo `platform_ps4_core_clock.cpp` experimental usa `sceKernelGetProcessTimeCounter` e frequência da API nativa do PS4.
- `sleep_ns` chama `sceKernelUsleep` com microssegundos, arredondados para cima.
- Sem alterar `tools/etapa38/platform_ps4_core.cpp` nem os homebrews anteriores.
- Fórmulas em `clock_math.h`, com teste C++ `test_clock_math.cpp` executado pelo GitHub.
- Declara `RELOGIO=OK` somente quando esperar 2ms produz delta de 1,5–50ms (faixa tolerante).
- Resultados de FPS são marcados inválidos enquanto o relógio não for validado.
- Log inclui frequência de ticks, contador bruto, delta e modo (NORMAL/CARGA).

## Critérios de aprovação
- O workflow compila e produz o PKG homebrew independente.
- No PS4, em Klog: `KAZUMA47: TIMER_NATIVE_HZ`, `CLOCK_TENTATIVA` e `RELOGIO=OK`.
- Se `RELOGIO=FALHA`, **não interpretar os valores de FPS**. Não afirmar correção sem log.
- Esperar 30 s em NORMAL, alternar para CARGA com triângulo, esperar 30 s; quadrado repete diagnóstico e X testa entrada.
- Não executar Castlevania, modificar saves, nem conter arquivos comerciais.

## Próximo passo
Depois de verificar a temporização nativa em hardware, focar no runtime original (ligação de componentes do jogo, entrada e renderização). Não confundir FPS do homebrew com FPS do jogo.
