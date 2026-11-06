# Operação Castlevania — Etapa 81: AOT real sem falsos positivos

## Confirmado com relatório e backup privados

- `subsdk0`: **14.173 funções**, **902.188 instruções reconhecidas**, **0 não tratadas**, **73 unidades C++** geradas.
- `sdk`: **40.112 funções**, **1.654.429 instruções reconhecidas**, **1 não tratada**, **136 unidades C++** geradas.
- O `sdk` foi preservado em tar.gz privado no Google Drive; não publicá-lo, nem enviar código gerado ao GitHub.
- Em `code_132.cpp`, a instrução `stg x8, [x8]` está no endereço guest `0x62a7f0`, **dentro de laço com incremento de 16 bytes**, e o emissor colocou `nx::unimpl(...)`. Não há base para chamar o fluxo de 100% suportado.
- `STG` é uma instrução ARM de *memory tagging*. Não substituir automaticamente por `nop`: a política de tags do guest e a configuração MTE precisam de análise antes de concluir que o efeito não é observado.

## Correção do gate

O script `tools/etapa79/aot_private.py` agora preserva a distinção entre `aot_generated` e `all_instructions_supported`. O primeiro significa apenas que o recompilador criou os arquivos e retornou sucesso. O segundo exige explicitamente `unhandled 0` na primeira linha de `report.txt`. Caso a linha do relatório não seja reconhecida, a ferramenta **falha fechada**.

## Próxima execução privada

A Etapa 81 usa um notebook Colab separado (artefato privado da conversa) para:

1. Localizar o backup do SDK existente no Drive privado.
2. Recompilar e salvar `subsdk0` **somente se** não houver um backup íntegro.
3. Validar o NSO `main` por Build ID e SHA-256 fixados no perfil 1.1.0.
4. Invocar a CLI AOT original no Colab para `main`, com temporizadores/checagem de espaço e backup privado, e salvar relatório leve.
5. Não tentar link de PS4 com qualquer saída marcada como `unhandled > 0`.

**Ainda NÃO comprova:** compilação e link do jogo para PS4, solução de MTE, tradução completa NVN→SPIR-V, execução no console ou tela de créditos. `Kazuma Traduções` permanece nos arquivos próprios do runtime conforme Etapa 80, sem alterar o conteúdo original.
