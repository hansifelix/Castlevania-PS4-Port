# Castlevania PS4 — NVN original + vkloader oficial + Mesa/RADV real

## Progresso confirmado

- PR #123 compilou o NVN upstream, a ponte PS4 e o vkloader.c oficial
  do orbis-porting-kit v1.0.0, commit
  bdf17b594ba33dee266752f77cf87728130597e5.
- PR #124 adicionou o arquivo estático real libvulkan_radeon.a e libz.a
  do bundle orbis-sdk-v1, com SHA-256 fixado
  f4f079a4df334b46a76996f895283904283d6a006f97102aafaa53d4ecfc9622.
- Actions #42515971861 concluiu PASS_PARTIAL_RADV: os três provedores
  ICD estão definidos, vkGetInstanceProcAddr está definido e o objeto
  relocável contém o RADV real.

## O que o PASS não significa

O relatório de #42515971861 registrou 423 nomes de símbolos
indefinidos. O link foi ld.lld -r, não link executável. Não houve
VkDevice, swapchain, WSI, VideoOut, frame, EBOOT, PKG ou execução no PS4.

A ponte atual em tools/etapa62/ps4_vulkan_bridge.cpp solicita
VK_EXT_headless_surface e ignora native_window. Isso não apresenta
imagem na TV; o WSI RADV Orbis com sceVideoOutRegisterBuffers e
sceVideoOutSubmitFlip ainda precisa ser integrado ao caminho do projeto.

## Diagnóstico estrito da fatia isolada

A PR draft #127 tentou o link estrito da fatia GPU isolada, com
OpenOrbis v0.5.4 e libSceGnmDriver. Actions #42609853444 retornou
BLOCKED: 100 símbolos indefinidos reportados, zero bibliotecas ausentes,
e o linker atingiu o limite de 100 mensagens. Entre os primeiros
nomes estão nx::game::kInfo, nx::log e funções nx::nvn::ReplayScope,
astc_native e async_gpu. Esses nomes são provedores do runtime público
que não foram incluídos no pequeno conjunto de objetos dessa experiência.
O resultado não demonstra que o driver RADV esteja sem biblioteca;
demonstra que a fatia isolada não é um programa linkável.

A próxima medição útil deve combinar o conjunto público de runtime e
adaptadores PS4 com a fatia RADV antes de classificar dependências
externas restantes. Não substituir funções ausentes por stubs.

## Hardware

A tentativa de Etapa 63 no PS4 em 23/10/2026 saiu antes de Vulkan por
falha de carga de libSceFios2.prx (0xa0020102) e ausência de icon0.png.
Não há resultado do usuário para GIPA, INSTANCE, SURFACE, RADV, WSI,
VideoOut ou frame. A demonstração triangle verificada pelo autor
upstream em 17/09/2026 não é prova do pacote deste projeto.
