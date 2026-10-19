# Primeira análise do projeto — 19/10/2026

## Evidência obtida do APK fornecido

- APK analisado: `castlevania-full-desbloqueado.apk` (não redistribuído).
- `lib/arm64-v8a/libcastlevania.so`: **ELF64 AArch64**, tamanho descompactado ~310,25 MiB.
- Dependências dinâmicas Android (`readelf -d`): `libandroid.so`, `liblog.so`,
  `libaaudio.so`, `libmediandk.so`, `libm.so`, `libdl.so`, `libc.so`.
- `lib/arm64-v8a/libnximport.so`: ~0,95 MiB.
- `assets/spirv.zip`: ~26,07 MiB; pacote possivelmente relacionado a shaders.
- `assets/config.txt`: descreve o app como "Switch recomp on Android" e usa opções `NX_*`.
- Isso não prova disponibilidade do código C++ de recompilação nem portabilidade direta para PS4.

## Resultado decisivo

**O APK ARM64 NÃO pode ser usado como eboot.bin do PS4 x86-64.**
O código ARM64 gerado e o launcher de Android são binários. Precisamos do código-fonte
ou de uma etapa reprodutível de recompilação para gerar uma versão PS4, além de portar
serviços de entrada, áudio, arquivos, memória e NVN/Vulkan para o hardware AMD GCN.

## Referências técnicas, não substitutos automáticos

- https://github.com/BelmanteGu  — em 19/10/2026, perfil com 7 repositórios,
  sem código-fonte público identificável de Castlevania.
- https://github.com/iHaiDeeZ/SMW — referência de recompilação Switch para PS4.
- https://github.com/iHaiDeeZ/SMW/blob/main/docs/BUILDING.md — processo real usa
  código-fonte específico do jogo, clang/OpenOrbis, RADV e uma máquina de build.

## Etapas técnicas ainda BLOQUEADAS

1. Identificar código-fonte/publicação/licença ou técnica reproduzível da recompilação
   exata deste Castlevania. **Sem isso, não existe caminho direto para compilar o jogo.**
2. Confirmar versão exata de jogo suportada pela recompilação (base / update).
3. Implementar/runtime PS4 com Vulkan/RADV e bindings de I/O e memória.
4. Integrar/validar entrada DS4 (o mapeamento puro já foi prototipado e testado).
5. Compilar e validar `eboot.bin` real em ambiente com SDK/toolchain PS4.
6. Produzir e instalar pacote PKG contendo executável funcional, e testar no Slim.

## Segurança e licenciamento

Não enviar nem publicar `prod.keys`, `title.keys`, dados de jogos, APK modificado ou
bibliotecas compiladas do jogo. Use suas próprias cópias autorizadas.
O APK fornecido NÃO foi executado; sua segurança não foi atestada.

## Atualização v0.2 — inspeção da versão Switch

A captura do ZIP permite identificar os IDs `0100BA4026E94000` (base),
`0100BA4026E94800` (update) e `0100BA4026E95001` (DLC), mas não confirmar
os bytes dos pacotes. Foi incluído um validador PFS0 que não extrai arquivos,
sem abrir chaves. Mais detalhes: `versao_switch.md`.

Existe ainda a possibilidade de adaptar **código-fonte específico de Castlevania**
se o desenvolvedor o disponibilizar; usar as bibliotecas compiladas do Android
não substitui esse código-fonte. O PS4 SMW é outra implementação, para outro jogo.
