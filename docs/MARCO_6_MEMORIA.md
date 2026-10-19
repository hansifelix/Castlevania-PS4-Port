# Marco 6 — Sondagem limitada de memória do PS4 (v1.0)

Este marco desenvolve um pequeno teste de APIs POSIX de memória. **Nao e a memoria completa de Castlevania, nao executa o jogo e nao modifica o PKG visual.**

## Por que precisamos disso?

O runtime aberto de Castlevania para macOS usa um espaco de enderecos virtual do sistema Switch de ate 39 bits e regioes fixas para modulos, heap, alias, pilha e kernel. A implementacao upstream em `runtime/src/memory.cpp` depende de `nx::plat::reserve`, `commit` e `decommit`; a implementacao PS4 equivalente ainda nao existe.

A reserva de dezenas de GiB de espaco *virtual* nao e o mesmo que ter essa RAM fisica. Entretanto, **nao sabemos ainda se o processo PS4 aceita as posicoes e os tamanhos necessarios**, nem se o backend grafico pode ser adaptado. Nao tentar `MAP_FIXED` ou reservas gigantes diretamente no console: isso poderia atingir regioes de outros componentes do processo.

## O que esta prova faz

- Usa `mmap(nullptr, ...)` para deixar o SO escolher onde alocar; jamais usa `MAP_FIXED`.
- Testa `mprotect`, escrita/leitura nas extremidades e `munmap` de apenas 4 KiB, 64 KiB e 1 MiB.
- Rejeita entradas nulas ou superiores a 1 MiB.
- Testa nativamente essas chamadas em Linux; em seguida, tenta compilar um `eboot.bin` *independente* para PS4 com OpenOrbis.
- Nao empacota PKG e **nao executa codigo no console**. Um check verde prova somente teste Linux e compilacao PS4; nao compatibilidade de memoria do PS4 real.

## Depois do check verde

1. Conferir se as funcoes POSIX linkam com o SDK.
2. Construir um teste **com resultado visivel na tela** ou log recuperavel no PS4, mantendo os recursos do jogo fora do pacote.
3. Quando esse teste em hardware for feito, investigar regioes fixas especificas do runtime, sem mapear por forca enderecos usados.
4. Separadamente, avaliar se a traducao NVN → Vulkan funciona no ambiente grafico do PS4. A passagem para o jogo completo exige ainda o codigo recompilado e seus dados; nada disso esta presente aqui.

## Seguranca e distribuicao

Nao inclui NSP, APK, chaves, arquivos comerciais nem executavel do jogo. Mantem o repositorio visual privado intocado. Nao instalar `eboot.bin` isolado; ele e apenas um artefato para desenvolvedores.
