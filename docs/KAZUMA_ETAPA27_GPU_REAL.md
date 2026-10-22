# Kazuma Port Games BR — Etapa 27: primeiro teste GPU REAL (somente preparacao)

Esta etapa constrói um **PKG novo e independente** do **triângulo Vulkan público** de `orbis-ports/orbis-porting-kit/examples/triangle`. Não há arquivos, imagens, código recompilado, ROM ou assets de Castlevania.

## Dados e garantias limitadas

- Origem do exemplo / scripts: `orbis-ports/orbis-porting-kit` commit `213b0c38ff25ea7ca402c8844a6494086d0f1cae`.
- SDK, overlay e Mesa/RADV no conjunto publicado `orbis-sdk-v1`.
- `Title ID`: `BREW91240`; `TITLE`: `Kazuma GPU Vulkan Test 07`; versão `01.00`.
- PKG com content ID `IV0000-BREW91240_00-KAZUMAVULKANGPU1`.
- O GitHub produz pacote e hashes mas **não executa nem instala nada no PS4**.
- A instalação em hardware deve ser decidida só após os checks passarem e o arquivo final ser revisado. O teste pode congelar o console, exibir tela preta ou falhar; nenhuma garantia de segurança absoluta.
- Um triângulo exibido na televisão comprova somente a cadeia gráfica deste **exemplo mínimo** naquela configuração. Não comprova shaders NVN, `vkCmdBeginRendering`, carregamento do jogo, áudio ou menu de Castlevania.

## Como verificar, sem instalar

1. Os dois checks da PR precisam estar verdes e o artefato precisa conter um só PKG nomeado `IV0000-BREW91240_00-KAZUMAVULKANGPU1.pkg`.
2. Confirmar SHA-256 e tamanho com `relatorios/etapa27/RESULTADO_pkg.json` e `PKG_SHA256.txt`.
3. Não instalar automaticamente. Se decidir fazer o teste, faça com saves importantes previamente copiados e sem dispositivos externos contendo únicos arquivos importantes conectados; encerrar com o menu PS se necessário. Se travar, não insistir em testes repetidos.
4. Resultado esperado do exemplo: um triângulo gráfico renderizado na TV; uma tela preta, erro Vulkan ou travamento não prova impossibilidade do port, apenas falha deste caminho de teste.

**Etapa 27 NÃO é port de Castlevania.**
