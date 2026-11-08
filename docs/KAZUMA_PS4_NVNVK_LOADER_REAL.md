# Operação Castlevania PS4 — conectar NVN original ao loader Vulkan real

## Objetivo (bloqueio gráfico, não demonstração cosmética)

A etapa 62 tinha um adaptador real de superfície Vulkan,
`tools/etapa62/ps4_vulkan_bridge.cpp`, mas deixava
`nx::plat::ps4::vk_get_instance_proc_addr()` **sem implementação**.
A etapa 63 só o implementava dentro do executável isolado
`gpu_bridge_probe.cpp`, sem ligá-lo ao código NVN que recebe comandos
reais da GPU emulada.

O novo `src/ps4/platform_ps4_vulkan_loader.cpp` fornece **essa mesma
ligação ao símbolo externo real** `vkGetInstanceProcAddr`.
O arquivo só compila com a macro explícita
`KAZUMA_PS4_REAL_VULKAN` e **não devolve ponteiro falso, null ou stub**.
O destino do link estrito deverá ser o bundle
`orbis-ports/orbis-porting-kit` (`orbis-sdk-v1`) que inclui Mesa/RADV e
vkloader; **OpenOrbis v0.5.4 isolado não fornece a implementação Vulkan**.

## Novo teste integrado

O CI compila para `x86_64-pc-freebsd12-elf` com OpenOrbis v0.5.4,
Clang 18, headers Vulkan Khronos fixados e upstream MIT pinado:

- `runtime/src/nvn/nvn_vk.cpp`: dispositivo, submissão e apresentação NVN;
- `runtime/src/nvn/nvn_shaders.cpp`: tabela/identificação de shaders;
- `runtime/src/nvn/nvn_gpu_pick.cpp`: escolha de GPU;
- `tools/etapa62/ps4_vulkan_bridge.cpp`: superfície/headless real;
- `src/ps4/platform_ps4_vulkan_loader.cpp`: ponte para vkloader real.

Um `ld.lld -r` verifica se os provedores Vulkan e
`nx::nvn::gpu_submit`/`gpu_present` foram definidos no MESMO objeto.
O verificador exige que `vkGetInstanceProcAddr` permaneça importado
(e não fabricado dentro do nosso conjunto), pois a definição real virá
do bundle de GPU no link executável.

**Limites:** a aprovação é só compilação e link relocável.
Ainda NÃO há link Mesa/RADV estrito, VkDevice/swapchain em hardware,
NVN completo, SPIR-V do jogo, frame visível, EBOOT/PKG ou teste no PS4.
Os dados AOT privados continuam fora do CI. Nenhuma ROM, shader
comercial, imagem, arquivo gigante ou material foi enviado ao Google
Drive. Os objetos de compilação permanecem temporários no runner.
