# KAZUMA ETAPA 64 — Triângulo Vulkan em TV PS4

## Correção de estado — 09/11/2026

A tentativa da Etapa 63 feita pelo usuário no PS4 em **23/10/2026**
não chegou à inicialização Vulkan. O Klog registrou falha de carga de
libSceFios2.prx (PRX_SCE_MODULE_LOAD_ERROR, código 0xa0020102) e
ausência de icon0.png; o aplicativo saiu antes de GIPA, VkInstance,
superfície ou enumeração da GPU. Portanto, não é correto afirmar que
esta instalação do projeto já inicializou VK_EXT_headless_surface ou
enumerou RADV Liverpool no console.

O exemplo triangle do orbis-ports/orbis-porting-kit, commit
213b0c38ff25ea7ca402c8844a6494086d0f1cae, foi verificado em hardware
pelo autor upstream em 17/09/2026. Isso não valida o nosso pacote,
a nossa integração nem o Castlevania.

## Implementação pretendida

A arquitetura do exemplo upstream usa o WSI RADV Orbis, que encaminha
vkQueuePresentKHR para sceVideoOutRegisterBuffers e sceVideoOutSubmitFlip.
O código atual do projeto ainda usa VK_EXT_headless_surface na ponte
pública; o parâmetro native_window é ignorado. A integração de WSI
VideoOut real ainda precisa ser feita e testada.

## Estado público em 09/11/2026

- PR #124: o arquivo Mesa/RADV real e zlib foram incluídos num link
  relocável com NVN e vkloader; os três provedores ICD foram encontrados.
- Actions #42515971861: PASS_PARTIAL_RADV, mas 423 nomes de símbolos
  continuaram indefinidos. Não foi link executável.
- PR #127 / Actions #42609853444: o link estrito da fatia isolada
  NVN/RADV ficou BLOCKED com 100 símbolos indefinidos reportados.
  Os primeiros exemplos pertencem ao runtime público ausente nessa
  fatia (nx::game, nx::log e nx::nvn), não demonstram por si só uma
  biblioteca RADV ausente.
- Não há nesta etapa prova de VkDevice, queue, swapchain, shader,
  draw, flip, frame visível, EBOOT/PKG do jogo ou gameplay no PS4.

## Critérios futuros no Klog

Os marcadores abaixo são metas de aceitação futuras, não resultados já obtidos:

- KAZUMA64: ok vkCreateInstance e vkCreateHeadlessSurfaceEXT
- KAZUMA64: ok vkCreateDevice e vkCreateSwapchainKHR
- KAZUMA64: ok vkCreateGraphicsPipelines
- KAZUMA64: setup complete - presenting
- KAZUMA64: frame 0 presented

Tela preta, travamento ou falha de flip no hardware devem ser registrados
sem adivinhar e sem repetir tentativas arriscadas.
