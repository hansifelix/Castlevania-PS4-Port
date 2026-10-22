# Kazuma Port Games BR — Etapa 17: paginas de memoria do processo homebrew

## Objetivo estritamente limitado
O Test 06 usa o homebrew conhecido das Etapas 12–16, sem ROMs, NSP ou APK.
Adicionamos um **teste de 64 KiB via mmap** com endereco escolhido pelo SO:

1. `mmap(nullptr, 65536, PROT_NONE, MAP_PRIVATE | MAP_ANON, -1, 0)`;
2. `mprotect` para leitura/gravação;
3. escrita/leitura de padrao conhecido com verificacao integral;
4. `mprotect` para PROT_NONE, **sem ler novamente**;
5. `munmap` para devolver a regiao.

Exibe `PAGINAS PS4: OK` **somente** se as cinco fases passarem no PS4.
Falhas nao geram tentativa automatica de novo mapeamento e a tela mostra FALHA.
O teste fica limitado a 64 KiB e nao requer privilégio de kernel.

## Importante: o que nao prova
As assinaturas das interfaces `nx::plat::reserve/commit/decommit` do codigo
publico sao verificadas em tempo de compilacao por `static_assert`, **mas as
implementacoes nao foram feitas nem invocadas**. A memoria do jogo exige
enderecos guest fixos, muito maiores, e possiveis conflitos com o mapa do PS4.
Nao reservar enderecos fixos indiscriminadamente, nao usar MAP_FIXED, nao
modificar kernel, firmware ou paginas pertencentes a outros processos.

O Test 06 e um experimento independente, **nao inicializa o jogo**. CI verde
apenas comprova compilacao, link e empacotamento. O Title ID exclusivo e
`BREW91239`; Testes 01–05 nao sao substituidos. Qualquer teste no console deve
ocorrer apenas apos revisar os logs. Se travar ou der erro, NAO insistir e
fechar pelo botao PS quando possivel. Guardar saves e backup do PKG funcional.
