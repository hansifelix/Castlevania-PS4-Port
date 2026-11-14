# Kazuma Etapa 96 — candidatos de provedores SDK/runtime para símbolos AOT

**Status:** ferramenta privada de inspeção somente leitura; testes públicos usam apenas fixtures sintéticas.

## Objetivo

Depois do inventário privado ELF das Etapas 91–95, comparar nomes indefinidos sem provedor AOT interno com símbolos definidos nas bibliotecas e objetos do SDK OpenOrbis e do runtime PS4.

A comparação usa nomes exatos retornados por `nm`; identifica candidatos, não prova compatibilidade ABI.

## Execução privada

Com o relatório privado completo da Etapa 95 e bibliotecas/objetos correspondentes à mesma versão de toolchain:

```bash
python3 tools/etapa90/private_aot_sdk_provider_audit.py \
  --inventory "/caminho/privado/RELATORIO_ETAPA92_BINDINGS_COMDAT_PRIVADO_v2.json" \
  --provider-root "openorbis=/caminho/privado/OpenOrbis/lib" \
  --provider-root "runtime=/caminho/privado/runtime-ps4" \
  --nm llvm-nm \
  --report "/caminho/privado/RELATORIO_ETAPA96_PROVEDORES_PRIVADO.json"
```

Repita `--provider-root LABEL=PATH` para cada raiz que realmente participará do link. Os rótulos devem ser únicos. Se a ferramenta disponível se chamar `nm`, use `--nm nm`.

O relatório contém símbolos C++ mangled e caminhos locais: mantenha-o fora do repositório, de artefatos públicos e do chat. Relatórios anteriores são preservados automaticamente com sufixos `_v2`, `_v3` etc.; `--overwrite-report` é explícito.

## Endurecimento da Etapa 96

A revisão da própria ferramenta encontrou dois riscos de classificação que poderiam produzir falsos candidatos:

- O formato `nm -A` identifica o membro de um archive, por exemplo `lib.a[member.o]`. A versão inicial descartava esse identificador e podia tratar duas definições em membros diferentes do mesmo `.a` como uma única candidata. Agora cada definição mantém o membro; duas definições distintas são classificadas como **ambíguas**, mesmo dentro do mesmo archive.
- Raízes sobrepostas podiam fazer a mesma biblioteca física aparecer mais de uma vez. A varredura agora deduplica a mesma definição física, sem apagar diferenças entre membros, e não segue diretórios/arquivos symlink.
- Qualquer diagnóstico em stderr, saída malformada, timeout ou erro de leitura marca a varredura como incompleta. O CLI retorna código não zero; não transforma leitura parcial em sucesso.
- O relatório permanece fora das raízes inspecionadas e não sobrescreve arquivos anteriores sem opção explícita.

A suíte pública agora cobre membro duplicado no mesmo archive, raízes sobrepostas, symlinks e diagnóstico de `nm` em stderr, além dos casos anteriores. Ela usa apenas bibliotecas e inventários fictícios.

## Segurança e limites

- Aceita somente inventário completo: cobertura dos 1.916 índices, metadados das definições duplicadas completos e nenhum objeto inválido.
- Lê bibliotecas/objetos com `nm -A -g --defined-only --format=posix`; não extrai arquivos, não compila, não liga e não toca no PS4.
- Ignora symlinks e arquivos fora das extensões suportadas (.a, .so, .o, .elf, .prx, inclusive versões .so.N).
- Registra bibliotecas que não puderam ser inspecionadas; execução com erros não é completa.
- Nome idêntico é apenas candidato. A ferramenta não verifica relocations, versão de símbolo, convenção de chamada, layout de tipos, dependências transitivas nem aceitação pelo linker.
- O JSON privado contém nomes e caminhos locais. Somente contagens agregadas podem sair do ambiente privado.

## Próximo passo

Executar novamente o inventário privado Etapa 91/95 no conjunto AOT completo, depois cruzá-lo localmente com as bibliotecas da mesma versão do SDK OpenOrbis e runtime PS4. Revisar cada candidato com headers, versões e contratos ABI correspondentes antes de qualquer link privado controlado. Não preencher lacunas com stubs nem declarar port jogável com base em contagens ou CI sintética.
