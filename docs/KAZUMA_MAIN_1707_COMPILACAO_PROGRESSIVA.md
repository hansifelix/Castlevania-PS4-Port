# Kazuma Traduções — MAIN AOT: compilação incremental privada (07/11/2026)

O usuário já concluiu a compilação e o **link parcial** do `subsdk0` (73 objetos) e do `sdk` (136 objetos). O módulo `main` é o maior bloqueio remanescente de AOT.

## Auditoria de código real, feita somente em ambiente privado

- Arquivo de origem verificado por SHA-256: `main-20261106-033625-061622-privado.tar.gz`, hash `b308aab38edf15a38bff512c6cbb4319b44fade2347bb705938ae802928917cc`.
- **1.707/1.707** arquivos C++ `code_NNN.cpp`, total expandido do backup de aproximadamente **1,93 GB**.
- AOT `report.txt` registra **401.987 funções**, **20.769.983 instruções tratadas**, **duas não tratadas**: `mov`.
- Incompatibilidades da libc++ OpenOrbis: **479** chamadas `std::countl_zero` em **106** C++ e **124** chamadas `std::popcount` em **38** C++. União **133 arquivos**, pois 11 usam ambas.
- Duas `nx::unimpl` correspondentes a instruções vetoriais AArch64 SVE (`mov z24.b, p3/m, #4` e `mov z12.b, p3/m, #6`) localizadas em `code_000.cpp`. **Não são MOV escalar simples; não trocar por NOP ou zero**. O restante do módulo também contém `nx::unimpl` de guardas de exceção e `udf`, que não provam execução necessária no gameplay.
- Backups e C++ proprietários **não** foram publicados neste repositório.

## Nova ferramenta pública de validação

`tools/main_compile/main_cpp_preflight.py` permite auditar um backup que o usuário possua localmente. Ela verifica o SHA-256 quando fornecido, recusa duplicatas, links e arquivos incompletos, e emite somente contagens, nomes genéricos e indicadores. Os seis testes `tests/test_main_cpp_preflight.py` usam exclusivamente pequenos tarballs sintéticos.

## Laboratório privado preparado

Notebook entregue na conversa, fora do GitHub: `Kazuma_Castlevania_MAIN_1707_Compilacao_Progressiva_Celular.ipynb`.

- Mesma toolchain usada nos dois módulos anteriores: **OpenOrbis v0.5.4, Clang 18** (SHA-256 fixado) e upstream no commit `4043f21bb4f656d34cd17ba070238c7728d00631`.
- O notebook calcula SHA-256 do backup antes de usar qualquer C++; extrai apenas os arquivos do intervalo a processar, sem descompactar os quase 2 GB de uma só vez.
- Cada execução tenta **no máximo 192 unidades**, divididas em lotes de **6** e com limite de tempo após o término de cada lote. A correção temporária das funções `countl_zero` e `popcount` é aplicada somente em cópias no Colab; o backup original fica inalterado.
- Todo lote com objetos compilados é salvo imediatamente no Drive privado, com manifesto SHA-256 por arquivo e upload verificado.
- Um relatório de etapa com nome baseado no conteúdo registra os índices tentados e as falhas, sem recomeçar do índice zero em cada nova sessão. Se a execução for interrompida antes do relatório, lotes previamente salvos no trecho são recuperados com validação de hash.
- Os erros são registrados individualmente; **ser tentado não significa ter compilado**. Uma vez percorridos os 1.707, qualquer falha será investigada em rodada de correção dedicada.

**Status em 07/11/2026:** auditoria e notebook preparados, **compilação real do main ainda não executada**, link parcial do main NÃO realizado, sem eboot/PKG/gameplay. Somente os dois módulos anteriores passaram na compilação real e no link relocável.
