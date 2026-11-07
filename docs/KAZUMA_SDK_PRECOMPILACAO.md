# Castlevania PS4 — preflight para compilar o SDK AOT verdadeiro

## Análise privada concluída em 7/11/2026

Arquivo analisado: backup privado `sdk-20261106-030016-359871-privado.tar.gz` já existente no Google Drive do usuário. SHA-256 conferido localmente: `bbb8814ac843b36ad107d09289b630a58482d78e134c0be6b574ba7b6b7cecac`. **O arquivo não foi enviado ao GitHub.**

- **136** unidades `code_NNN.cpp` verificadas;
- **42** delas usam `std::countl_zero`, somando **691 chamadas**. A libc++ OpenOrbis v0.5.4 não fornece essa função diretamente na configuração utilizada no `subsdk0` (Etapas 84–85). O novo laboratório aplica o substituto já testado, **somente em cópias temporárias dos 42 arquivos**;
- **879** ocorrências estáticas de `nx::unimpl`: 575 guardas padrão do tratamento de exceções, 301 `udf`, 2 palavras não decodificadas e 1 `stg`, no `code_132.cpp`.
- Relatório AOT upstream: 40.112 funções, 1.654.429 instruções tratadas, **1 instrução não tratada**, do tipo `stg`.

**Não é correto** dizer que as 575 guardas de exceção são 575 falhas ativas. Tampouco podemos converter `stg` em `nop` automaticamente: a semântica MTE do guest ainda não foi validada.

## Código público e ensaio privado

`tools/sdk_compile/sdk_cpp_preflight.py` lê backups locais, verifica contagem íntegra, recusa arquivo alterado (quando informado o SHA-256), links e duplicatas, e emite exclusivamente metadados (nomes genéricos `code_NNN.cpp`, contagens e categorias). Testes automatizados usam somente arquivos C++ fabricados para o teste.

O notebook privado `Kazuma_Castlevania_SDK_136_CPP_Pronto_Celular.ipynb`, entregue na conversa (não enviado ao repositório), está preparado para:

1. Conectar o Google Drive privado, localizar o backup original e conferir seu SHA-256;
2. Preparar checkout fixado do upstream e OpenOrbis v0.5.4/Clang 18;
3. Testar a compatibilidade CLZ (incluindo zero) com a toolchain PS4;
4. Compilar sequencialmente os **136** C++ em lotes de 6, com progresso visível;
5. Salvar cada lote de objetos ELF no Drive privado, com hashes para recuperação em nova sessão, mesmo que um dos arquivos falhe;
6. Gerar o `Kazuma_Castlevania_SDK_136_Resultado.json` para diagnóstico. O download local usa o alias `colab_files` para não repetir a colisão de variável `files`.

## Limites

**A compilação real do SDK ainda NÃO foi executada**. O notebook e o preflight foram preparados, mas só o usuário pode autorizar a execução na sessão Colab. Nenhum objeto do SDK foi compilado/ligado no runtime PS4 nesta alteração. AOT emitido não significa semântica completa de STG, link estrito, eboot, PKG nem gameplay.

O futuro link com os demais módulos deverá reutilizar os 73 objetos já aprovados do `subsdk0`, as três tabelas reais e o registro `main/sdk/subsdk0`. Não repetir a extração ou a recompilação AOT original sem necessidade.

A marca **Kazuma Traduções** identifica apenas o trabalho próprio do port.
