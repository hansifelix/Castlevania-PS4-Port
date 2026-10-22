# Kazuma Port Games BR — Etapa 22: auditoria GPU NVN/Vulkan → PS4

## Por que importa
O runtime publico tem uma ponte NVN para Vulkan. Os testes anteriores no PS4
exibiram uma interface 2D propria e **nao executaram esta ponte**. O objetivo
e avaliar as dependencias de entrada do Vulkan para priorizar proximos testes.

## Fontes e limites
- Codigo do runtime publico `SwonDev/cstlvnia-blmont-to-macos`, commit
  `4043f21bb4f656d34cd17ba070238c7728d00631`, `runtime/src/nvn/*.cpp`
  e `runtime/src/platform.h`.
- Pacote OpenOrbis v0.5.4 `toolchain-llvm-18.tar.gz`, SHA256
  `3c7cd5bb593ca74fa1c13fd59f3938dc0fc07985167f7275063019e63abe4526`.
- Alternativas **de terceiros, nao instaladas/verificadas no PS4 deste usuario**:
  [mesa-ps4](https://github.com/orbis-ports/mesa-ps4) e
  [vulkan-ps4](https://github.com/PS4-OpenGNM/vulkan-ps4). Os repositorios
  publicos **nao** garantem que esses backends suportem o runtime NVN.

## O que a auditoria faz
- Varre o codigo C++ de NVN em busca de nomes de funcoes `vk...` e os agrupa
  por recursos. Isto e **amostragem heuristica**, NAO a lista completa de
  requisicoes dinamicas (o runtime pode usar tabela de ponteiros `vk_gen`).
- Registra se `vulkan.h`/`libvulkan*` constam do SDK OpenOrbis instalado no runner.
- Produz `GPU_DIAGNOSTICO.md` e `gpu_dependencias.json`.
- Registra `go_no_go: INDETERMINADO`; nao compila um backend, nao gera ELF/PKG,
  nao testa shaders, GPU real, menu original nem dados do jogo.

## Proximos gates
1. Disponibilizar uma implementacao de Vulkan que de fato rode no PS4,
   com apresentacao no VideoOut, e medir versao/extensoes.
2. Verificar as extensoes e formatos usados por NVN/shaders, e o suporte real
   desse backend — nao basta compilar o cabeçalho Vulkan.
3. Integrar a camada de memoria guest, loader, threads e servicos.

**Este experimento e somente um levantamento de dependencia tecnica.**
