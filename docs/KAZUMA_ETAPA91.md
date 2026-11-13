# Etapa 91 — inventário privado de símbolos AOT

## Objetivo

Depois da Etapa 90-C confirmar a integridade estrutural dos 1.916 objetos, esta etapa lê as tabelas ELF de símbolos dos módulos MAIN, SDK e subsdk0 para identificar:

- Símbolos globais/weak definidos por cada objeto;
- Símbolos globais/weak indefinidos que cada objeto requer;
- Nomes com candidatos de definição em outros objetos AOT, no mesmo ou em outro módulo;
- Símbolos ainda sem candidato dentro do inventário AOT;
- Para cada símbolo indefinido, candidatos definidos em outros objetos AOT, discriminados pelo objeto consumidor.

O parser lê ELF64 little-endian ET_REL x86-64 e mantém os nomes mangled exatos. Ele lê um membro por vez de ZIP/TAR.GZ, sem extrair os objetos para o Drive. Os testes públicos incluem arquivos ZIP e TAR.GZ sintéticos para conferir essa leitura sem extração. O CI executa os cinco testes do inventário de símbolos, além da suíte CTest e da auditoria estrutural anterior, sempre com dados fictícios.

## Segurança dos dados

O relatório JSON contém nomes privados de símbolos mangled e caminhos relativos. **Não enviar esse JSON ao GitHub, não anexar ao chat e não compartilhar publicamente.** Compartilhar somente um resumo agregado manualmente, sem nomes de símbolos nem caminhos.

A ferramenta não compila, não liga, não cria EBOOT/PKG, não modifica os arquivos de entrada e não inicializa o PS4.

## Execução privada

No Colab/PC, com o repositório clonado e a pasta privada montada:

```bash
python3 tools/etapa90/private_aot_symbol_inventory.py \
  --root "/caminho/privado/Kazuma_Traducoes_AOT_Privado" \
  --report "/caminho/privado/RELATORIO_SIMBOLOS_ETAPA91_PRIVADO.json"
```

O caminho de `--report` deve ficar fora da pasta auditada. O resumo impresso no terminal contém apenas contagens; o JSON privado contém os nomes dos símbolos.

## Como interpretar

- `undefined_symbol_provider_candidates`: para cada símbolo indefinido, mapeia cada objeto consumidor aos outros objetos AOT que definem o mesmo nome. São candidatos, não prova de resolução correta. As métricas agregadas contam pares objeto-símbolo, provedores únicos por par, ambiguidades e candidatos entre módulos.
- `cross_module_definition_candidates`: símbolos para os quais há definições em mais de um módulo AOT.
- `undefined_without_aot_provider`: nomes indefinidos que não aparecem como definição no inventário AOT.
- `multiply_defined_symbols_within_module`: nomes definidos em mais de um objeto do mesmo módulo, úteis para investigar colisões.
- `duplicate_definition_profiles`: para cada nome duplicado entre objetos, mantém somente no JSON privado os bindings ELF, tipos, visibilidades, índices de seção e presença em grupos COMDAT por objeto. As métricas agregadas distinguem definições GLOBAL/WEAK/GNU_UNIQUE e se as definições pertencem a grupos COMDAT.
- `invalid_objects`: objetos cujas tabelas ELF não puderam ser analisadas.

## Limites

Um nome idêntico não comprova compatibilidade ABI. Esta etapa não valida relocations, versões ELF, convenções de chamada, layouts de estruturas, dependências transitivas nem aceitação pelo linker OpenOrbis. A nova inspeção de binding/tipo/visibilidade/COMDAT melhora a classificação das definições repetidas, mas não substitui a execução de um link com a toolchain alvo. Depois do inventário, os candidatos devem ser confrontados com a mesma versão da toolchain, headers e bibliotecas OpenOrbis; só então se prepara um link privado controlado.

**Status desta etapa:** ferramenta e testes públicos usam apenas ELF sintético. A execução real nos backups privados ainda depende de rodar o comando no ambiente que contém esses backups.
