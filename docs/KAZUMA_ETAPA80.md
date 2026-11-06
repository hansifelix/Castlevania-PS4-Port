# Kazuma — Etapa 80: assinatura de autoria da adaptação para PS4

## Marca

**Kazuma Traduções** (UTF-8, com cedilha e til) é a marca solicitada para identificar o trabalho da equipe no **port experimental para PS4**. Não atribui propriedade do jogo, história, personagens, música, gráficos ou marcas originais à equipe.

A implementação inclui:

- `src/runtime_bridge/kazuma_branding.cpp` e `.hpp` com três funções C ABI: `kazuma_port_brand()`, `kazuma_port_credit()`, `kazuma_original_game_notice()`.
- Teste C++ no CTest garantindo a grafia e separação de créditos.
- O fluxo do runtime PS4 da Etapa 75 compila `kazuma80_brand.o` e o inclui no link parcial `kazuma75_runtime_partial.o`; há verificação do símbolo e do texto com `llvm-nm` e `strings`.
- Não há dependência de ativos comerciais ou logotipos nos testes.

## Onde a marca aparece (e onde ainda não)

**Já existe no código do port e no objeto do runtime PS4 quando o fluxo da Etapa 75 é executado.** Não foi incorporada a uma tela de jogo funcionando, pois a renderização nativa do jogo ainda não está operacional. O ponto de integração futura de créditos é a interface do port, via `kazuma_port_credit()`, em uma apresentação que não se confunda com créditos da desenvolvedora original.

Uma string embutida em um executável não impede que alguém a remova. Histórico de commits, licença sobre código original e distribuição com autoria clara são recursos de atribuição; não fornecem proteção técnica infalível.

## Situação AOT

O primeiro AOT completo relatado pelo usuário para `subsdk0` já produziu 73 arquivos C++ e relatório com 14.173 funções, 902.188 instruções tratadas e 0 não tratadas. Ainda faltam `sdk`, `main`, link completo PS4, shaders e teste real.

Os fontes gerados a partir dos NSOs comerciais devem permanecer em armazenamento **privado**, nunca nos Actions, PRs ou repositório público.

**Status:** marca integrada ao fluxo de código nativo. Exibição dentro de gameplay: **não testada/não pronta**.
