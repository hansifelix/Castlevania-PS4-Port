# Marco 8 — ponte gráfica NVN/Vulkan (Castlevania PS4 v1.2)

## Objetivo verificável desta fase

Confrontar automaticamente a **interface gráfica pública** do runtime de Castlevania com a **implementação PS4 de referência** de *Super Mario Bros. Wonder*, sem utilizar os arquivos do jogo e sem afirmar compatibilidade em hardware.

O runtime Castlevania usa `nx::plat::vulkan_get_instance_proc_addr`, `vulkan_surface_extension`, `vulkan_create_surface` e rotinas de janela, e a GPU NVN é traduzida para Vulkan. O port do SMW PS4 demonstra outra adaptação dessa família de runtime: Mesa/RADV + WSI própria + `sceVideoOut*`. **Não é possível simplesmente copiar um driver e afirmar que funciona**, pois versões do runtime e shaders são diferentes.

### Fontes de referência (revisões fixas)

- Runtime: `SwonDev/cstlvnia-blmont-to-macos` commit `4043f21bb4f656d34cd17ba070238c7728d00631` (projeto independente, código MIT).
- Port PS4: `iHaiDeeZ/SMW` commit `2e8c2adfac0675a960192336ca26249019eca489` (`patches/wonder-ps4.patch`). Ler os créditos e as licenças antes de aproveitar código.

### O que o GitHub Actions vai verificar

1. Existência das assinaturas dos três pontos de entrada Vulkan no runtime de Castlevania e implementação PS4 referencial.
2. Outras funções de janela/tela (`window_size`, `screen_size`, etc.) na referência PS4.
3. Presença de um WSI PS4 com extensão headless, swapchain, VideoOut e `ac_ps4_submit_flip`.
4. A existência de **três** módulos em Castlevania: `main`, `sdk` e `subsdk0`. SMW usa um conjunto diferente; o terceiro precisa de suporte.
5. Emissão de `graficos-auditoria.json` e `graficos-auditoria.md` com cada resultado e as lacunas.

### O que um check verde NÃO significa

- Não é uma compilação de gráficos para PS4.
- Não prova que Mesa RADV e Vulkan estejam carregados no console.
- Não inclui AOT, dados, shaders, NSP, APK, ROM ou chaves.
- Não faz nenhuma imagem de Castlevania aparecer na TV e não estima FPS.

### Próximos passos técnicos após esta auditoria

1. Criar um backend de plataforma PS4 específico do runtime de Castlevania e resolver diferenças de interface.
2. Preparar a toolchain com Mesa RADV/WSI e construir um diagnóstico Vulkan de verdade.
3. Testar criação de instância, GPU, fila gráfica e apresentação na tela; registrar erros no PS4.
4. Separadamente integrar os três módulos do jogo recompilados e validar recursos/shaders privados, antes de falar em gameplay.

Não publicar dados de jogo ou chaves no GitHub. O projeto e o teste são experimentais e independentes dos titulares de Castlevania.
