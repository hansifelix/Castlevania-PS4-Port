# Kazuma — Etapa 88: validar endereços AOT dentro da seção TEXT (07/11/2026)

## Continuação concreta da Etapa 87
A Etapa 87 conferia 14.173 registros da tabela AOT real de `subsdk0` (fonte **privada**). Este complemento, programado inteiramente com dados sintéticos, estabelece um novo contrato de execução:
cada offset de função AOT precisa pertencer ao intervalo TEXT válido de um **módulo já registrado**.

## Código e provas
- `src/port_core/aot_text_bounds.hpp` e `.cpp` acrescentam `check_aot_text_bounds` ao Kazuma Port Core público.
- São verificados: módulo conhecido; offset/tamanho de TEXT sem overflow, alinhados a palavra de 4 bytes e contidos na imagem; ao menos uma função; função alinhada, única, ordenada e no intervalo TEXT.
- Cada offset válido também é resolvido como endereço guest pelo `GuestModuleIndex`. Endereços inválidos **falham**, não são ignorados.
- `tests/test_aot_text_bounds.cpp` exercita 15 casos sintéticos (incluindo endereços de fronteira, offset de fora, registro repetido, desalinhamento e overflow). CTest roda em Linux/host.
- Nenhum dado, imagem, ROM, NSO, C++ proprietário ou chave de jogo foi versionado.

## Importante
Este teste é **um contrato genérico**, não significa que o TEXT real 1.1.0 foi auditado com esse novo componente ou que exista execução de jogo no PS4.

Próximo teste *real* (privado): obter o intervalo TEXT de `nx::ModuleInfo` gerado por upstream, verificar os offsets contra o índice, compilar e ligar a tabela com headers oficiais. A execução e o teste de GPU continuam tarefas separadas.
