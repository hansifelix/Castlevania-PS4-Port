# Kazuma — Etapa 46 — Benchmark da infraestrutura, SEM JOGO

## Motivação
O hardware executou a Etapa 45: Klog indicou inicialmente `RELOGIO=FALHA`, em seguida `RELOGIO=OK`, `ARQUIVO=OK`, `PASTA_VAZIA_REJEITADA=OK` e entrada do botão X. A causa exata da falha inicial do relógio ainda é desconhecida.

## Objetivo da Etapa 46
Validar novamente o relógio (4 tentativas, logs com timestamp bruto) e medir a cadência dos frames **deste homebrew** num PS4 real. Não executa nem mede Castlevania.

## Tela e controles
- Marca `KAZUMA PORT GAMES BR` pequena; visual autoral escuro/dourado, sem assets de terceiros.
- Mostra FPS (média móvel por blocos de 120 frames), tempo médio, pior tempo e quantos frames passaram de 40 ms.
- **Triângulo:** alterna normal/carga sintética 2D de 1600 retângulos por frame e zera a janela de medição.
- **Quadrado:** repete o diagnóstico de arquivo/diretórios/relógio.
- **X:** confirma input.
- **PS:** fecha pelo sistema.
- Klog em stdout: `KAZUMA46: CLOCK_TENTATIVA=...`, `KAZUMA46: PERF FPS_X10=...`.

## Precauções e limitações
- Não modifica saves nem diretórios; lê uma fixture própria em `/app0`.
- O resultado é restrito à rota OpenOrbis/Scene2D do aplicativo de teste, **não significa FPS do jogo Castlevania**.
- Os indicadores FPS incluem apresentação/espera de frame, não apenas processamento da CPU; o modo carga sintética não reproduz o motor do jogo.
- Se ocorrer crash, não repetir testes indefinidamente: analisar Klog e logs.
- Checks verdes atestam compilação offline e produção do pacote, não resultado no hardware.
- Próxima prioridade depois desta etapa: voltar à ligação de código do runtime/jogo e às dependências reais, antes de discutir FPS real do jogo.
