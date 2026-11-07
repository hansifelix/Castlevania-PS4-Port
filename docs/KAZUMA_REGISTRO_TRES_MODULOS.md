# Castlevania PS4 — Registro autêntico dos três módulos (07/11/2026)

## Objetivo concreto, sem novo número de etapa

O upstream fixado em `4043f21bb4f656d34cd17ba070238c7728d00631` declara em `games/castlevania/modules.cmake`:

```cmake
set(NX_MODULES main sdk subsdk0)
```

O CMake upstream gera `nx::linked_modules()` referenciando `nx_module_main`, `nx_module_sdk`, `nx_module_subsdk0`. O arquivo público `src/runtime_bridge/linked_modules_castlevania.cpp` replica **exatamente esse contrato e essa ordem**, sem símbolos fracos ou registros falsos. Todos os três `nx_module_*` terão que ser definidos pelas tabelas AOT **privadas verdadeiras** no link final.

## Teste público reproduzível (sem ROM)

O workflow `.github/workflows/kazuma-etapa88-loader-abi.yml` compila `registry.o` para `x86_64-pc-freebsd12-elf` com OpenOrbis v0.5.4 e Clang 18, exige no `nm` as três referências indefinidas no objeto isolado, liga com **três fixtures sintéticas**, verifica a resolução dos símbolos e roda um contrato C++ de host que valida:

- Exatamente três posições, não nulas, sem duplicatas;
- Ordem `main`, `sdk`, `subsdk0`;
- A função `nx::linked_modules()` é exportada com assinatura e ABI compatíveis.

O CI não recebe `table.cpp` real, `code_*.o` ou chaves. Seu pacote de artefatos públicos inclui somente `loader.o`, `memory.o`, `ps4_memory.o`, `registry.o` e hashes SHA-256.

## Verificação adicional feita em ambiente privado

Os três arquivos originais do usuário foram recuperados do Drive privado e suas tabelas AOT inspecionadas:

| Módulo | Entradas `FuncEntry` reais | `report.txt` | Compilação de tabela |
|---|---:|---:|---|
| main | 401.987 | 401.987 | OK, Clang host |
| sdk | 40.112 | 40.112 | OK, Clang host |
| subsdk0 | 14.173 | 14.173 | OK, Clang host |
| **Total** | **456.272** | **456.272** | **3/3** |

Compilamos as tabelas em diretório privado usando **Clang do host com declarações reduzidas de structs públicos e base `NX_BASE` equivalente ao upstream**. O `registry.o` foi compilado pela toolchain oficial OpenOrbis no CI e teve SHA-256 validado após download. Rodamos o link `ld.lld -m elf_x86_64 -r` entre `registry.o` e os **três objetos reais de tabela**:

- Link relocável: **aprovado**;
- Tamanho do combinado: **63.463.472 bytes**;
- Referências indefinidas `nx_module_main`, `nx_module_sdk`, `nx_module_subsdk0`: **zero**;
- Referências de funções AOT ainda indefinidas: **401.987 main + 40.112 sdk + 14.173 subsdk0 = 456.272**;
- Os 73 objetos de código já compilados de `subsdk0` **não** foram incluídos nesse link específico; adicionar esses objetos deve resolver as 14.173 referências próprias desse módulo.

**Limite crucial:** compilar com headers mínimos do host não equivale a compilar todas as tabelas com headers OpenOrbis reais. Este é apenas um teste de layout/assinatura/registro e link relocável, não um executável. Não se trata de testes em PS4. As tabelas, C++ e ELF comercial derivado permaneceram exclusivamente no ambiente privado e não foram versionados.

## Link privado adicional com 73 objetos reais e runtime

Sem recompilar nenhum dos arquivos anteriores, recuperamos e validamos via SHA-256 **73 objetos ELF reais** do `subsdk0`, além dos objetos públicos `loader.o`, `memory.o`, `ps4_memory.o` compilados no CI com OpenOrbis.

O comando `ld.lld -m elf_x86_64 -r` ligou **3 tabelas AOT reais + registry.o + 73 objetos subsdk0 + loader + memory + PS4 memory**, sem erro. ELF resultante: **122.577.216 bytes**, mantido só em ambiente privado. No `nm -C -u`:

| Referência a função AOT | Indefinida no teste |
|---|---:|
| main | 401.987 |
| sdk | 40.112 |
| subsdk0 | **0** |

Os três símbolos `nx_module_*`, `nx::call` e `nx::unimpl` também deixaram de aparecer como indefinidos. Além dos 442.099 corpos de funções não compilados dos módulos `main`/`sdk`, restam **97 outros símbolos externos** de runtime e bibliotecas, esperados neste link **-r**. As tabelas foram recompiladas em Clang host com structs ABI equivalentes, portanto este não é teste definitivo do conjunto completo OpenOrbis nem prova de execução no console.

**Próximo bloqueio mensurável:** compilar e ligar as 136 unidades C++ do `sdk`, resolver semântica STG, depois as 1.707 unidades de `main` e os MOV não suportados. A integração de serviços e NVN/SPIR-V permanece pendente.

## Bloqueio real seguinte

1. Fazer um link privado **com registro + três tabelas reais + 73 objetos reais subsdk0** usando versões compiladas com ABI uniforme e reportar os módulos ainda indefinidos. Em particular, não fingir que `main` e `sdk` estão compilados porque suas tabelas já foram ligadas.
2. Compilar os **136 C++ do sdk** e investigar o `stg` não tratado.
3. Compilar gradualmente os **1.707 C++ do main** e investigar as duas formas `mov` não tratadas.
4. Integrar runtime real completo, memória, serviços, bibliotecas, NVN/Vulkan/SPIR-V, testar link estrito e boot. Somente depois gerar PKG jogável.

**Crédito:** `Kazuma Traduções` identifica o trabalho de port, nunca a autoria da obra original.
