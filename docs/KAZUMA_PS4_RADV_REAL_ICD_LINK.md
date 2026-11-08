# Operação Castlevania PS4 — ligação NVN até o ICD Mesa/RADV real

## O que foi integrado nesta etapa (#124)

A PR #123 já compilava o runtime NVN do upstream, a ponte Vulkan PS4
e o `vkloader.c` oficial, mas `vk_icdGetInstanceProcAddr`
**continuava indefinido**. Aqui a fonte desse símbolo é o **arquivo
estático verdadeiro `libvulkan_radeon.a`**, incluído no link parcial
junto dos seis objetos reais do PR #123.

O GitHub Actions baixa o bundle PS4 `orbis-sdk-v1` (mesmo da Etapa 63)
com **SHA-256 exato**
`f4f079a4df334b46a76996f895283904283d6a006f97102aafaa53d4ecfc9622`.
A compilação usa os headers Vulkan **da mesma build Mesa** que produziu
o driver, evitando misturar layouts de estruturas incompatíveis.

Fontes e bibliotecas combinadas no `ld.lld-18 -r`:
- `nvn_vk.cpp`, `nvn_shaders.cpp`, `nvn_gpu_pick.cpp` do upstream MIT fixado;
- `ps4_vulkan_bridge.cpp` e `platform_ps4_vulkan_loader.cpp` do projeto;
- `vkloader.c` original do kit PS4 (tag assinada v1.0.0);
- `libvulkan_radeon.a`, de Mesa/RADV real, ligado com
  `--whole-archive` como prescreve o kit;
- `libz.a` da **mesma** árvore Mesa, necessário ao cache de shaders.

O novo gate exige exatamente uma definição das três funções
`vk_icdGetInstanceProcAddr`, `vk_icdGetPhysicalDeviceProcAddr`
e `vk_icdNegotiateLoaderICDInterfaceVersion`, além de todas as
interfaces anteriores da ponte NVN/vkloader. Referência ICD ainda
indefinida ou duplicada é **falha**, não resultado aprovado.

**Este é um link relocável e NÃO um executável.** A inclusão do driver
não confirma inicialização, Vulkan WSI, sceVideoOut, apresentação de
frame, CPU STG/SVE, shader SPIR-V do Castlevania nem código AOT privado.
Todos os objetos ficam somente no runner descartável do GitHub; nenhum
artefato binário é publicado ou enviado ao Google Drive.

## Próximos bloqueios após passar no CI

1. Resolver imports SDK/musl/libc++/orbis-compat surgidos do driver, com
   análise de link estrito e biblioteca de WSI.
2. Validar extensão `VK_EXT_headless_surface`, swapchain e VideoOut
   **em hardware PS4**, não apenas pela presença dos símbolos.
3. Integrar o módulo AOT privado e shaders traduzidos (fora do GitHub)
   e tratar CPU SVE/STG sem usar NOPs.
4. Testar compatibilidade de memória e frame sincronizado, depois
   construir EBOOT/PKG do jogo somente quando apropriado.
