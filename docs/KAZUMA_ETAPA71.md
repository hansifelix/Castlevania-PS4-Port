# 🏰 Kazuma Etapa 71 — threads REAIS do runtime público

A Etapa 70 identificou apenas arquivos NSP do jogo base/atualização; não há ExeFS `main`, `sdk`, `subsdk0` e RomFS extraídos. Os arquivos originais não devem ser publicados.

O relatório real da Etapa 50 registrou 268 símbolos externos antes e depois das 3 APIs de memória (3 resolvidos + 3 novos), incluindo 18 interfaces `nx::plat` pendentes. Em particular, `start_thread`, `exit_thread` e `yield` estavam indefinidos.

Esta etapa compila implementações nativas POSIX para PS4 dessas três funções e tenta novamente o link ESTRITO de `nx::boot()` com os objetos reais do runtime. O serviço de threads aborta explicitamente se não conseguir criar a thread. Não se usa thread sintética ou retorno de sucesso falso. Uma prova comportamental Linux verifica criar, executar e finalizar uma thread.

O GitHub Actions registra em `etapa71/LEIA_PRIMEIRO.txt`, `RELATORIO.json`, `COMPILACAO.log` e `LINK_ESTRITO.log` se os símbolos saíram do objeto e quais dependências restantes bloqueiam o ELF. Checks verdes atestam apenas os passos executados, NÃO execução no PS4 nem Castlevania jogável.

**Portões de saída:** implementação compila no PS4 SDK, símbolos 3 deixam de estar indefinidos, testes Linux passam, relato explícito do link final e lista de pendências. Se falhar, o check deverá ficar vermelho — não corrigir por stubs.

**Limites:** 3 APIs de host ≠ o runtime completo. Ainda faltam jogo AOT ARM64→C++, recursos RomFS, serviços, NVN real, áudio e testes no console. Sem PKG nesta etapa e sem dados comerciais no GitHub. Não executar nem descriptografar NSPs nesta etapa.
