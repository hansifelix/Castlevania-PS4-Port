# Kazuma Port Games BR — Etapa 63: ligar a ponte Vulkan ao Mesa/RADV real

> **Atualização de estado — 2026-11-08**
>
> A Etapa 63 começou como uma sonda Vulkan independente. O trabalho posterior avançou a integração de código: o PR [#124](https://github.com/hansifelix/Castlevania-PS4-Port/pull/124), incorporado à `main` pelo commit `a00d175968365fa8d455044ac9d57caa47e1ce28`, integrou o arquivo real Mesa RADV ICD ao caminho NVN Vulkan/vkloader.
>
> Isso é integração de fonte e infraestrutura de ligação, **não** uma prova de link executável final. O gate RADV distingue explicitamente `PASS_PARTIAL_RADV` de sucesso final: exige os três provedores ICD reais e a ligação NVN/vkloader, mas não declara executável estrito, EBOOT/PKG ou execução de GPU.
>
> O PR [#125](https://github.com/hansifelix/Castlevania-PS4-Port/pull/125) adicionou CI leve para os três gates sintéticos. A execução #1 terminou com sucesso. Esse resultado valida os cenários de teste dos verificadores; **não** significa que um binário PS4 real foi compilado ou executado.
>
> **Estado confirmado:** integração de fonte Mesa RADV ICD no caminho NVN/vkloader; CI sintético dos gates aprovado.
>
> **Ainda não confirmado:** link executável estrito com o conjunto completo de dependências; criação de EBOOT/PKG atual; inicialização da Vulkan no PS4; apresentação de frame; jogo jogável.
>
> A descrição abaixo registra a hipótese e o plano originais da Etapa 63. Referências a uma compilação verde ou a uma sonda de diagnóstico devem ser lidas como critérios/plano daquela etapa, não como prova de que os resultados acima foram alcançados.

## Hipótese testada

A ponte `nx::plat` compilada na Etapa 62 precisa ser conectada a um provedor Vulkan real. Esta etapa usa o bundle *fixado* `orbis-sdk-v1`, composto de OpenOrbis, overlay e Mesa/RADV/WSI PS4 compatíveis, e liga `ps4_vulkan_bridge.cpp` a `ps4-vkloader` / `libvulkan_radeon.a`.

A sonda de GPU é um app PS4 independente: ela cria uma `VkInstance`, pede a `VK_EXT_headless_surface` através da nossa ponte, enumera um dispositivo físico e consulta as propriedades da superfície. Não possui jogo, arte, dados do Switch ou shaders de Castlevania.

**Critério original da sonda:** uma compilação verde comprovaria linkagem e criação do EBOOT e PKG de diagnóstico, mas não que as operações Vulkan funcionaram no console. Só logs vindos de hardware permitem declarar `INSTANCE=OK`, `SURFACE=OK`, `GPU=...`, `WSI_CAPS=OK` e `PONTE_GPU_REAL=OK`.

## Entradas e proveniência

- `tools/etapa62/ps4_vulkan_bridge.cpp` na branch principal deste repositório.
- `orbis-ports/orbis-porting-kit` release `orbis-sdk-v1`, SHA256 `f4f079a4df334b46a76996f895283904283d6a006f97102aafaa53d4ecfc9622`. O kit é arquivado; usa-se o bundle emparelhado e verificável como baseline, sem downloads de partes incompatíveis.
- `ps4-vkloader` e RADV embutidos nesse bundle. Nenhuma definição de função Vulkan simulada foi incluída no binário PS4.

## Instalação manual SOMENTE depois da revisão dos artefatos

O pacote não se instala automaticamente. É homebrew de diagnóstico, mas pode encerrar com tela preta ou falha no console se as dependências gráficas não funcionarem. Salve seus dados importantes e remova dispositivos contendo a única cópia de arquivos antes do teste. Ao iniciar a sonda, a tela pode permanecer preta — os resultados aparecem no Klog (`sceKernelDebugOutText`). Se necessário, feche pelo botão PS. Não repita tentativas em caso de travamentos graves.

Os principais marcadores no Klog são `KAZUMA63: BOOT`, `GIPA`, `INSTANCE`, `SURFACE`, `GPU`, `WSI_CAPS`, `PONTE_GPU_REAL`.

### O que permanece pendente

- A sonda não apresenta frames na tela e não mede FPS.
- Não existe integração com `nvn_vk.cpp` completo nem recompilação dos módulos `main`, `sdk`, `subsdk0`.
- Não há versão jogável, menu original, tradução nem garantia de conclusão até Halloween.
