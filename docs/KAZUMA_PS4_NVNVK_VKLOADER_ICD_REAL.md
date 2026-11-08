# Castlevania PS4 — NVN original + vkloader oficial até o ICD Mesa/RADV

## Progresso concreto após a PR #122

A PR #122 compilou e ligou cinco fontes públicas, mas deixou
`vkGetInstanceProcAddr` **indefinido**. Portanto o código gráfico ainda
não estava unido ao carregador Vulkan efetivamente usado no PS4.

Esta etapa compila também `vkloader/vkloader.c` do
`orbis-ports/orbis-porting-kit` na tag assinada **v1.0.0**, commit
**bdf17b594ba33dee266752f77cf87728130597e5** (MIT).
É o código C genuíno do adaptador estático para PS4, que define
`vkGetInstanceProcAddr`, `vkCreateInstance`, e utiliza
`vk_icdGetInstanceProcAddr` do verdadeiro Mesa/RADV.

O novo workflow OpenOrbis v0.5.4 + Clang/LLVM 18 compila e liga,
num mesmo ELF relocável, **seis arquivos**, os cinco já aprovados da
PR #122 mais o `vkloader.c` oficial. O verificador exige:

- `nx::nvn::gpu_submit` e `nx::nvn::gpu_present` presentes;
- o wrapper PS4 `nx::plat::ps4::vk_get_instance_proc_addr()` definido;
- `vkGetInstanceProcAddr` **DEFINIDO**, exatamente uma vez, não mais
  listado como símbolo indefinido;
- `vk_icdGetInstanceProcAddr` **INDEFINIDO**: prova de que o próximo
  vínculo necessário é a implementação real do ICD Mesa/RADV e não
  uma função fictícia criada no nosso código;
- resolução de `vkCreateInstance` e funções exportadas por `vkloader.c`.

Os testes de falha detectam ausência, duplicação e definições falsas
do símbolo ICD. Nenhum objeto AOT comercial, shader do jogo, PKG,
EBOOT ou artefato binário é publicado; tudo é compilado no runner
temporário, **sem usar Google Drive**.

## O que ainda não é verdade

Esta ligação é um **link parcial `ld.lld -r`**; não inclui ainda o
arquivo `libvulkan_radeon.a` com o ICD, nem verifica o ABI com os
headers *pareados* do Mesa, o link estrito, dispositivo físico,
swapchain, apresentação de um frame ou estabilidade no console.

O caminho correto para o próximo teste é o bundle fixado
`orbis-sdk-v1` com **Mesa/RADV + zlib + SceGnmDriver + SceVideoOut**
(em versões pareadas); o kit documenta essas dependências.
O compilador e os headers Vulkan Khronos usados aqui validam o
contrato público Vulkan, **não substituem** um teste contra os
headers da build Mesa real.

O bundle/kit está arquivado, mas é a base compatível com as versões já
usadas nas etapas 62–63. A migração para orbsdk seria decisão separada,
não uma troca silenciosa de ferramenta em meio ao port.

Um check verde nesta PR não significa jogo iniciando nem gráfico pronto.
