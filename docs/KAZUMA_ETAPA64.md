# KAZUMA ETAPA 64 — Triangulo Vulkan em TV PS4

## Motivacao
A Etapa 63 inicializou VK_EXT_headless_surface, instância e enumerou RADV Liverpool
na GPU real do console. Nao testou VkDevice, queue, swapchain, shaders, draw ou flip.

## Implementacao
Porta exemplo MIT do kit publico orbis-ports/orbis-porting-kit,
`examples/triangle/` no commit `213b0c38ff25ea7ca402c8844a6494086d0f1cae`.
Usa o MESMO bundle fixado da Etapa 63 para evitar misturar ABI de drivers.
Em PS4, a implementacao WSI do RADV Orbis interpreta vkQueuePresentKHR com
sceVideoOutRegisterBuffers / sceVideoOutSubmitFlip.

## Metas no Klog
- KAZUMA64: ok vkCreateInstance e vkCreateHeadlessSurfaceEXT
- KAZUMA64: ok vkCreateDevice e vkCreateSwapchainKHR
- KAZUMA64: ok vkCreateGraphicsPipelines
- KAZUMA64: setup complete - presenting
- KAZUMA64: frame 0 presented

## Limites
Checklist verde do GitHub nao demonstra frame real nem jogo portado.
O programa de teste nao contem Castlevania e nao estima FPS do jogo.
No hardware, tela preta, trava ou falha de flip devem ser documentadas sem adivinhar.
O exemplo foi verificado pelo autor no hardware em 2026-09-17; o nosso pacote nao foi.
