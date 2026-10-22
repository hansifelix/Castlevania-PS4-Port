# Kazuma Port Games BR — Etapa 25: construir a primeira dependencia real do Mesa PS4

## Objetivo

Depois da auditoria de Vulkan da Etapa 24, testar **compilacao de fato** de `orbis-compat`,
uma das duas dependencias identificadas no codigo publico da versao PS4 do Mesa RADV.
Esta etapa vai alem da analise de texto: faz cross-compilacao para `x86_64-pc-freebsd12-elf`
e valida a biblioteca `liborbis-compat.a` e os simbolos definidos.

## Fontes fixadas

- `orbis-ports/orbis-compat` commit `6922a7b6f4291a28edd239f1a4db50ed7aa00359`.
- OpenOrbis Toolchain v0.5.4, tar `toolchain-llvm-18.tar.gz`, SHA256
  `3c7cd5bb593ca74fa1c13fd59f3938dc0fc07985167f7275063019e63abe4526`.
- O compilador sera o clang e llvm do Ubuntu 24.04 do GitHub Actions, não do Galaxy A73.

## Limites de escopo

1. **NAO compila Mesa RADV**, nem shaders NVN.
2. **NAO gera ELF/PKG** para instalar no PS4 e nao toca nos arquivos do jogo.
3. O runtime Castlevania e o loader permanecem sem integracao comprovada.
4. Se o cross-build da dependencia falhar, ler `BUILD.log`; NAO fazer merge automatico.
5. Sucesso na compilacao prova apenas que esta dependencia funciona com o ambiente de build.

## Proxima prova

Verificar compilacao completa do driver Mesa com suas dependencias pinadas e, em seguida,
projetar smoke-test grafico de Vulkan em hardware, revisando riscos antes de gerar PKG.
