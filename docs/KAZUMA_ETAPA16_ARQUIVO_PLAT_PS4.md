# Kazuma Etapa 16 - leitura de arquivo pelo runtime (subconjunto nx::plat)

O Test 05 preserva os testes anteriores, integra `nx::plat::fopen_utf8`
por `std::fopen` no OpenOrbis e testa a leitura de um arquivo de texto
100% sintetico localizado em `/app0/kazuma_stage16.dat` (fallback relativo).
O PKG inclui a fixture `KAZUMA_STAGE16_RESOURCE_OK\n` gerada neste repositorio.

## Resultado esperado

`NX PLAT ARQUIVO: OK` significa apenas que o homebrew abriu e leu os
bytes exatos da fixture pelo adaptador `nx::plat::fopen_utf8`.
`FALHA` indica que devemos verificar caminho `/app0`, montagem do PKG,
leitura e tratamento de erros, sem repetir a instalacao automaticamente.

## O que NAO testa

Nenhum recurso original do Castlevania; nenhum RomFS; nenhum jogo
recompilado; nenhuma GPU NVN; sem Vulkan, audio, memoria fixa, threads,
carregador, integracao completa da interface nx::plat ou menu real.
O teste nao usa arquivos comerciais nem chaves e nao modifica arquivos
do sistema. CI verde = apenas compilacao e empacotamento offline.

Novo Title ID `BREW91238`, independente dos outros homebrews.
A instalacao no PS4 e opcional e so deve ocorrer apos revisar CI.
