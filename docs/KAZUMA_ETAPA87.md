# Kazuma — Etapa 87: conectar tabela AOT ao código compilado do subsdk0

## Resultado testado (06/11/2026)

A Etapa 86 havia conseguido ligar **73 objetos C++ compilados** em um ELF relocável. A Etapa 87 acrescenta a tabela `table.cpp` produzida pelo recompilador e verifica que a tabela contém **14.173 funções** únicas, coerentes com `report.txt`.

Inspeção privada:

- Fonte AOT: backup do `subsdk0` versão 1.1.0, SHA-256 `0320bad0c5c3ba5d2571534f47e27be8be2830d803d306bf20d735911491ef1e`.
- Dez lotes de backup de objetos verificados: **73/73** `code_NNN.o`, todos ELF64 x86-64 com hashes SHA-256 conferidos.
- Tabela real `table.cpp`: **14.173 entradas**, offsets únicos, `nx_module_subsdk0` exportado.
- Compilação local da tabela: **aprovada** com Clang 17 de host e cabeçalhos de estrutura equivalentes ao `runtime/include/nx/module.h` público. O header CPU desse teste foi mínimo, portanto o teste NÃO comprova integração dos headers completos.
- Link `ld.lld -m elf_x86_64 -r` de **74 objetos** (73 código + 1 tabela): **status 0**; combinado `61.401.728` bytes.
- Apenas seis símbolos externos persistem: `nx::call`, `nx::unimpl`, `ceil`, `floor`, `fma`, `trunc`.

Isso confirma a vinculação entre as referências da tabela e as funções AOT geradas, mas **não** comprova o carregador, os demais módulos, a GPU, a ABI PS4 completa, um eboot ou PKG.

## Código público da etapa

`tools/etapa87/check_aot_table.py` valida a relação entre `table.cpp` e `report.txt`, falhando caso existam entradas faltantes, duplicadas, incoerentes ou pertencentes a outro módulo. Testes sintéticos em `tests/test_aot_table_registry.py` não usam dados de jogos.

## Próxima verificação com toolchain oficial — notebook privado

Notebook `Kazuma_Castlevania_Etapa87_Tabela_Runtime_Celular.ipynb` entregue na conversa (não comitado no GitHub) usa o backup do usuário no Drive, checkout público fixado do recompilador e **OpenOrbis v0.5.4/Clang 18** para recompilar a tabela contra os headers oficiais `nx`, executar o link parcial e salvar somente metadados JSON no Drive privado.

**Não executar AOT com fontes comerciais em GitHub Actions.** O notebook contém IDs de pasta privada e deve permanecer fora do repositório público.

## Pendências reais

1. Validar a mesma compilação com headers públicos completos e compilador OpenOrbis no Colab; não anunciar aprovação antes do resultado.
2. Integrar o registro `nx_module_subsdk0` à lista de módulos do loader e fornecer `nx::call`, `nx::unimpl`, além de libm. **Não criar stubs de sucesso fictícios para forçar o link**.
3. Compilar `sdk` e `main` e tabelas, auditar `stg` e duas `mov` não tratadas.
4. Integrar serviços, memória, NVN/Vulkan/SPIR-V, áudio, vídeo e controles, só então tentar eboot/PKG funcional.

**Crédito:** `Kazuma Traduções` se aplica ao trabalho do port, não à autoria do jogo original.
