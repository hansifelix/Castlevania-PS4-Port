# Operação Castlevania — Loader e memória PS4 ligados ao AOT real

**Data da verificação:** 7 de novembro de 2026  
**Status:** link ELF **relocável**, não executável. Nenhum PKG, eboot ou gameplay.

## Objetivo — sem outra etapa numerada

Reduzir as referências indefinidas do link parcial dos arquivos reais `subsdk0` utilizando implementações existentes, sem criar stubs de sucesso.

Usamos três implementações concretas:

- `runtime/src/loader.cpp` do upstream público, commit fixado `4043f21bb4f656d34cd17ba070238c7728d00631`.
- `runtime/src/memory.cpp` do mesmo upstream, que define `nx::commit` e `nx::vm_set`.
- `tools/etapa50/platform_ps4_memory.cpp` deste repositório, que define `nx::plat::reserve`, `nx::plat::commit` e `nx::plat::decommit`.

O workflow público `.github/workflows/kazuma-etapa88-loader-abi.yml` agora compila os três arquivos com **OpenOrbis v0.5.4 / Clang 18**, exige os cinco símbolos definidos no `nm`, liga os três com um probe sintético e falha se esses símbolos continuarem indefinidos. O artefato público armazena somente `loader.o`, `memory.o`, `ps4_memory.o`, seus hashes e metadados de origem.

## Prova de integração privada com o código verdadeiro

Os dez arquivos de backup de `code_000.o` a `code_072.o` foram conferidos por SHA-256, cabecalho ELF64 x86-64 e origem AOT `0320bad0c5c3ba5d2571534f47e27be8be2830d803d306bf20d735911491ef1e`. Os três objetos públicos foram extraídos de artefato de CI com hashes verificados. Os links abaixo foram executados em diretório temporário privado e os objetos não foram versionados.

| Link relocável, mesmo conjunto de 73 AOT | Status | Símbolos indefinidos |
|---|---|---:|
| + `loader.o` | OK | 91 |
| + `loader.o` e `memory.o` | OK | 93 |
| + `loader.o`, `memory.o` e `ps4_memory.o` | OK | 95 |

Os totais sobem porque cada componente verdadeiro agrega suas próprias dependências de biblioteca; **não** são erros acumulados do jogo.

Na primeira adição, resolvemos `nx::commit(unsigned long, unsigned long)` e `nx::vm_set(unsigned long, unsigned long, unsigned int, unsigned int)`, introduzindo quatro dependências: `nx::linked_modules()`, `nx::plat::reserve/commit/decommit`.

Na segunda, resolvemos as três `nx::plat` sem stubs, introduzindo cinco interfaces C/POSIX: `madvise`, `mmap`, `mprotect`, `munmap` e `sysconf`. Elas são esperadas do sistema operacional / bibliotecas do PS4 e exigem **link estrito** com a toolchain e verificações na plataforma antes de se alegar execução.

O teste privado destas comparações usa **73 objetos de código**, sem acrescentar `table.cpp` nesta comparação. Portanto, **não comparar diretamente** estas contagens com as 94 referências da Etapa 89 (que incluía a tabela). O relatório anterior da Etapa 87 continua válido para a tabela de 14.173 funções.

## Próximos bloqueios que realmente importam

- Resolver `nx::linked_modules()` pelo arquivo `linked_modules.cpp` que o CMake original gera de `NX_MODULES main sdk subsdk0`. Esse registro **só será completo quando as três tabelas existirem**, não usar registro parcial enganoso.
- Compilar as tabelas e objetos AOT reais do `sdk` e do `main` e integrar a inicialização do guest ao runtime completo.
- Resolver as demais chamadas de plataforma, serviços, C++ e `libm` pelo link real, sem substituir funções faltantes por sucessos fictícios.
- Corrigir os `stg` e `mov` sem handler e auditar os `nx::unimpl` quando atingíveis.
- Desenvolver e validar NVN→Vulkan/SPIR-V, entrada, áudio e gerenciamento de memória no console.

**Não houve teste em hardware real nesta mudança.** O código AOT comercial permaneceu no ambiente de trabalho privado. Os créditos `Kazuma Traduções` continuam identificando apenas a adaptação, sem reivindicar autoria do título original.
