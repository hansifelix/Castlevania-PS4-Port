# Etapa 92 — triagem de símbolos AOT e definições duplicadas

## Escopo

Esta etapa parte do relatório privado produzido pela Etapa 91. Os nomes mangled e caminhos internos permanecem somente no Drive privado; este documento registra apenas métricas agregadas e evidências do código público.

A auditoria de entrada analisou 1.916/1.916 objetos ELF64 ET_REL x86-64, com cobertura completa dos índices MAIN, SDK e subsdk0, zero objetos inválidos e sem extração, compilação ou link dos backups privados.

## Referências indefinidas sem provedor no inventário AOT

Foram encontrados 39 nomes indefinidos sem definição nos três módulos AOT. A classificação por família é:

| Família | Quantidade |
|---|---:|
| Callbacks específicos do Castlevania | 13 |
| ABI C++ / unwind / inicialização estática | 10 |
| Runtime NX / CPU / exceções | 8 |
| Matemática | 6 |
| Operações atômicas | 2 |
| **Total** | **39** |

Os 13 callbacks do jogo correspondem a implementações públicas presentes nos oito arquivos `src/ps4/castlevania_*.cpp` examinados. O workflow `.github/workflows/kazuma-ps4-video-closure.yml` lista esses oito arquivos, compila-os para o alvo x86_64 FreeBSD/PS4 com OpenOrbis e executa um link relocável conjunto. O gate `tools/link/video_callback_closure.py` exige 13 callbacks e seis provedores internos de vídeo e falha se houver referências internas de callback/provedor pendentes.

**Limite da evidência:** a existência dos provedores no código e do workflow não equivale a um resultado CI aprovado nesta etapa, nem comprova que o objeto AOT privado já foi ligado a eles. O gate de vídeo declara explicitamente que não produz executável final, EBOOT/PKG nem prova de boot.

Os 26 itens restantes permanecem em triagem. A classificação de família não é prova de que uma biblioteca específica os exporta: cada símbolo deverá ser comparado com headers, bibliotecas e toolchain OpenOrbis fixados, incluindo versão, binding e convenção de chamada.

## Candidatos internos por objeto consumidor

O relatório privado possui 99.972 nomes indefinidos com candidatos no inventário AOT, distribuídos por 226.463 pares objeto consumidor/símbolo. Cada um desses pares tinha exatamente um objeto provedor candidato; não foi encontrado par com múltiplos candidatos nem candidato entre módulos.

Isso é uma propriedade do inventário por nome e localização, não prova de ABI, relocations corretas ou link concluído.

## Definições repetidas entre módulos

Foram identificados 93 nomes definidos em mais de um módulo:

| Distribuição entre módulos | Nomes |
|---|---:|
| MAIN + SDK + subsdk0 | 51 |
| MAIN + SDK | 40 |
| SDK + subsdk0 | 2 |
| **Total** | **93** |

A classificação por família dos 93 nomes é:

| Família | Nomes |
|---|---:|
| Primitivas de compatibilidade NX | 57 |
| Helpers de compatibilidade C++ / biblioteca padrão | 31 |
| Metadados RTTI / exceções | 3 |
| Runtime do compilador / unwind | 2 |
| **Total** | **93** |

Os inventários originais registraram também nomes repetidos dentro de cada módulo: MAIN 75, SDK 70 e subsdk0 46. Isso não deve ser somado diretamente aos 93, pois há sobreposição entre conjuntos.

**Risco ainda aberto:** o relatório original guardava nomes e localizações, mas não os metadados ELF necessários para decidir se as definições repetidas são fracas, fortes, protegidas ou membros de grupos COMDAT. Portanto, ainda não se conclui se essas repetições são seguras em um link monolítico.

## Instrumentação adicionada para a reauditoria

O parser agora registra, para cada definição, binding ELF (GLOBAL, WEAK ou GNU_UNIQUE), tipo, visibilidade, índice de seção e participação em grupo COMDAT. O JSON privado inclui perfis por definição duplicada, enquanto a saída agregada permite contar as categorias sem revelar nomes ou caminhos.

Os testes sintéticos agora cobrem:
- leitura dos metadados de binding, tipo e visibilidade;
- identificação de uma definição incluída em grupo COMDAT;
- resumo de definições repetidas com mistura de GLOBAL/WEAK e COMDAT/não-COMDAT;
- preservação dos testes anteriores de parsing e candidatos por objeto.

O notebook Colab da Etapa 91 já faz fetch da branch antes de executar. Portanto, uma nova execução usará a versão mais recente do parser.

## Próximas ações

1. Reexecutar o notebook no Drive privado e manter o JSON integral fora do GitHub e do chat.
2. Compartilhar somente os contadores agregados de binding, tipo, visibilidade e COMDAT para avaliar os 93 nomes repetidos.
3. Triar os 26 nomes restantes contra os exports reais do OpenOrbis/libc++ e runtime NX fixados.
4. Só então preparar um link privado controlado com a mesma toolchain e inspecionar relocations; não inferir EBOOT/PKG ou boot a partir de link parcial.

## Limites da etapa

Nenhum backup privado foi alterado. Nenhum objeto privado foi compilado ou ligado. Nenhum EBOOT, PKG ou teste de gameplay no PS4 foi produzido nesta etapa. A `main` permanece intocada; o trabalho está isolado na branch da Etapa 91/92.


## Correção após revisão do primeiro relatório Etapa 92

A primeira execução do notebook Etapa 92 identificou uma falha na agregação: o parser extraía os metadados por símbolo, mas a rotina que consolidava os objetos não os copiava para o acumulador global. Por isso, o JSON dessa primeira execução apresentou listas vazias de binding/tipo/visibilidade e zero entradas de metadados nos perfis duplicados. **Essas métricas não são utilizáveis e não devem ser interpretadas como ausência de COMDAT ou como definições fortes.**

Correção aplicada na branch: cada objeto agora transfere seus `defined_details` para o acumulador por nome e localização. O teste de auditoria ZIP/TAR sintético foi ampliado para exigir dois provedores duplicados com binding GLOBAL, tipo FUNC e visibilidade DEFAULT, além de conferir os contadores agregados. O relatório da primeira execução deve ser mantido como histórico inválido para essa parte; é necessário executar novamente o notebook atualizado.
