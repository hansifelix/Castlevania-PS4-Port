# Operação Castlevania — link real dos 1.916 objetos AOT e três tabelas (07–08/11/2026)

## Resultado obtido, sem publicação de código derivado do jogo

O ambiente privado do usuário recuperou **319 arquivos de backup**, e comprovou por SHA-256 do manifest e formato ELF relocável x86-64:

| Módulo | Lotes | Objetos | Funções definidas |
|---|---:|---:|---:|
| `main` | 285 | 1.707 | **401.987** |
| `sdk` | 24 | 136 | **40.112** |
| `subsdk0` | 10 | 73 | **14.173** |
| **Total** | **319** | **1.916** | **456.272** |

Todos os 1.916 objetos e 319 arquivos passaram na auditoria de hash e arquitetura. Nenhum objeto, tabela comercial, código AOT compilado ou binário combinado foi enviado ao repositório público.

## Links relocáveis, executados de verdade

1. `ld.lld -m elf_x86_64 -r` com **1.707 objetos** do `main`: **PASSOU**, saída 1.537.??? bytes (tamanho do link principal disponível no relatório privado).
2. Mesmo comando com **136 objetos** do `sdk`: **PASSOU**, saída **118.145.008 bytes**.
3. Mesmo comando com **73 objetos** do `subsdk0`: **PASSOU**, saída **59.286.112 bytes**.
4. Mesmo comando com **três módulos de código**: **PASSOU**, **1.714.491.776 bytes**, ainda sem tabelas.
5. Adicionadas **as três tabelas reais de funções AOT**, registro `nx::linked_modules()` e objetos públicos `loader.o`, `memory.o` e adaptador PS4: **PASSOU**, **1.754.832.448 bytes** (ELF tipo REL, sem entrypoint).

A compilação das tabelas `main/sdk/subsdk0` nesta sessão usou **Clang host com cabeçalhos reduzidos ABI-equivalentes** a `nx/module.h` público, e não a sysroot completa de OpenOrbis. O `loader.o`, `memory.o`, `ps4_memory.o` e `registry.o` foram compilados pelo workflow público original OpenOrbis v0.5.4/Clang 18, com hashes de artefatos verificados. **A ABI completa PS4 das tabelas ainda precisa de teste definitivo**; o sucesso em `-r` não garante execução.

`nm -C` no objeto combinado comprova os símbolos definidos:
- Exatamente **401.987** funções `main_*`, **40.112** `sdk_*`, **14.173** `subsdk0_*`.
- **Zero** funções guest `main_*`, `sdk_*`, `subsdk0_*` indefinidas.
- Os três `nx_module_*`, `nx::linked_modules()`, `nx::call`, `nx::unimpl`, `nx::commit` e `nx::vm_set` estão definidos.

### Símbolos externos restantes

`nm -u` bruto trouxe **122 entradas**, **119 nomes distintos**. Não é uma lista de 119 defeitos do jogo: cada componente adicional traz dependências de plataforma e bibliotecas.

A classificação automática dos **119 símbolos distintos** é:

| Categoria | Distintos |
|---|---:|
| Callbacks específicos `nx_castlevania_*` | 13 |
| Núcleo runtime `nx::` | 9 |
| Plataforma `nx::plat::` | 3 |
| Runtime C++ / RTTI / alocação | 48 |
| ABI C e unwind | 16 |
| C/libc/libm | 30 |

Auditoria de código upstream, pin `4043f21bb4f656d34cd17ba070238c7728d00631`, localizou callbacks de vídeo e resolução em `games/castlevania/resolution.cpp`, `video_options.cpp`, `loading_animation.cpp`. Os três arquivos são protegidos por **`#if defined(__APPLE__)`**. Não se pode chamá-los como implementações prontas para PS4 sem adaptar semântica, entrada e renderização.

Outros obstáculos confirmados: `STG` guest em `sdk/code_132.cpp`, duas instruções `MOV` SVE em `main/code_000.cpp`, inicialização, sincronização, `nx::game::kInfo`, serviços e NVN/Vulkan/SPIR-V.

### Instrumentação pública

`tools/link/aot_link_gate.py` recebe **apenas a saída textual de `nm`**, verifica contagem exata das 456.272 funções, resoluções de registro, `nx::call` e `nx::unimpl`, e falha quando falta qualquer símbolo. Seus testes usam unicamente dados sintéticos. Não toca ROMs, PKGs nem objetos compilados.

### Limites declarados

**Não** há link executável estrito, `eboot.bin`, PKG, teste de boot ou gameplay. A instrução `STG` e as duas `MOV` SVE continuam sem implementação semântica. O ELF de ~1,75 GB existe somente no ambiente privado de trabalho; não compartilhar nem publicar binário derivado do jogo.

**Próxima tarefa real:** integrar implementações de serviços runtime e resolver os 13 callbacks de vídeo com abordagem PS4, mantendo assinaturas e sem gerar stubs falsos só para satisfazer `nm`.
