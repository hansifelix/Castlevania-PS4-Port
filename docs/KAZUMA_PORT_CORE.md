# Kazuma Port Core — primeiro componente reutilizável (07/11/2026)

## Por que existe
O laboratório Castlevania já dispõe de `GuestMemoryPlan`, capaz de rejeitar
faixas de memória de convidado inválidas. Esta etapa acrescenta um índice **sem dados
do jogo** para registrar módulos `main`, `sdk`, `subsdk0` ou qualquer conjunto
de módulos com nomes, bases e tamanhos fornecidos pelo chamador. O índice pode
ser reaproveitado em experimentos com outros jogos sem duplicar as verificações.

## Implementado
- `src/port_core/guest_module_index.{hpp,cpp}`: registro ordenado de módulos;
  recusa nomes vazios/duplicados, tamanho zero, páginas inválidas, desalinhamento,
  transbordamento uint64 e intervalos sobrepostos;
  consulta de endereço de convidado para nome de módulo e offset relativo.
- Depende do planejador existente: `src/runtime_bridge/guest_memory_plan.*`.
- Testes com módulos **fictícios** e limites de intervalo em CTest, sem ROM/ExeFS.
- C++17 puro, sem dependência de APIs PS4, sistema operacional ou material proprietário.

## Como testar
```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 2
ctest --test-dir build --output-on-failure
```

## Importante: o que NÃO existe ainda
O índice **não reserva memória física**, não reloca NSO, não executa AOT,
não carrega `nx::ModuleInfo`, não traduz shaders, não acessa contas e não
produz `eboot.bin` ou PKG. É uma peça testável para evitar erros de
mapeamento antes de conectar os módulos reais do Castlevania.

Próxima integração de valor: ao validar um descritor `nx::ModuleInfo` na
etapa de loader, converter `base/size` em entradas do índice, rejeitar mapas
sobrepostos e verificar se os endereços de `nx_module_subsdk0` (Etapa 87)
pertencem à imagem declarada. Isso depende do resultado da compilação
privada com headers oficiais upstream e OpenOrbis. Não publicar o jogo.

## Novo projeto
Pesquisa de viabilidade de Honkai: Star Rail no PS4: issue #85.
Não confundir o laboratório público de infraestrutura com port já funcional,
nem prometer independência do xCloud até haver prova de gameplay real.
