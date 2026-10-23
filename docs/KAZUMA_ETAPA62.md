# Kazuma Port Games BR — Etapa 62: Vulkan REAL (cabecalhos) / ABI PS4

## Objetivo verificavel

1. Compilar o `tools/etapa62/ps4_vulkan_bridge.cpp` para **ELF64 x86-64** com alvo FreeBSD/PS4 do compilador e o **SDK OpenOrbis**.
2. Utilizar os **cabecalhos oficiais reais** do Vulkan-Headers fixados em commit, nao os cabecalhos de teste usados na Etapa 61.
3. Emitir `readelf`, `nm`, SHA-256 e um relatorio de simbolos (publicos e externos).
4. Rodar teste de contrato em Linux, isolado com funcoes simuladas (regressao da Etapa 61).

O arquivo-fonte define `nx::plat::vulkan_get_instance_proc_addr`, `vulkan_surface_extension` e `vulkan_create_surface` conforme `runtime/src/platform.h` do SwonDev (MIT). Chama `ps4::vk_get_instance_proc_addr` como dependencia EXTERNA: nao fabrica GPU real. Em teste, ela e simulada.

## O que o check verde nao prova

- `ps4::vk_get_instance_proc_addr` ainda nao esta ligado a Mesa RADV nem `VK_EXT_headless_surface` por um WSI PS4 real.
- Nao ha `eboot.bin`, PKG, renderizacao na TV, shaders do jogo ou menu do Castlevania.
- `main`, `sdk`, `subsdk0` continuam sem estar recompilados para x86-64 neste repositorio.
- `readelf` e `nm` devem identificar um OBJETO (`ET_REL`), nao um executavel (`ET_EXEC`).

## Proxima verificacao real

Integrar o provedor da funcao `ps4::vk_get_instance_proc_addr` com o Mesa/RADV + WSI PS4 **de uma toolchain autorizada, com licencas respeitadas**. Validar criacao de VkInstance, enumeracao de GPU, surface e apresentacao em hardware com logs. Em paralelo, resolver acesso licito aos tres modulos do jogo, sem publica-los.

Arquivos comerciais, NSP, NCA, ExeFS, APK e chaves **nao entram** neste repositorio.
