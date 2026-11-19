# Kazuma Studios — Etapa 98: provedores públicos do runtime em manifesto hash-only

## Objetivo

A Etapa 96 produziu um inventário hash-only das definições do OpenOrbis v0.5.4. O cruzamento privado de 18/11/2026 encontrou candidatos no SDK, mas não encontrou nele os nomes da classe nx_runtime. A Etapa 98 cria uma segunda raiz de provedores: os objetos públicos do runtime e os adaptadores PS4.

## Entradas fixadas

- Runtime upstream: SwonDev/cstlvnia-blmont-to-macos, commit 4043f21bb4f656d34cd17ba070238c7728d00631.
- OpenOrbis: v0.5.4, SHA-256 3c7cd5bb593ca74fa1c13fd59f3938dc0fc07985167f7275063019e63abe4526.
- Vulkan-Headers: KhronosGroup/Vulkan-Headers, commit acbb9391c0a597272800cd3f4363661c00a27c77.
- Target: x86_64-pc-freebsd12-elf, Clang 18.

A compilação produz 87 translation units do runtime, um objeto de metadados públicos de Castlevania e 14 adaptadores públicos PS4. São objetos ELF relocáveis individuais; não há AOT privado, ROM/NSP, assets do jogo, link de executável ou pacote.

## Saída e privacidade

O workflow Etapa 98 - public runtime provider symbol hashes percorre os 102 objetos e publica somente um JSON com:

- SHA-256 dos nomes exatos dos símbolos definidos;
- quantidade de definições e quantidade de objetos por hash;
- letras de tipo do nm, contagens agregadas e hashes canônicos dos conjuntos.

Não publica nomes de símbolos, caminhos, nomes de objetos, bytes de objetos ou dados AOT. O artefato public-runtime-provider-hashes tem retenção de sete dias. Os objetos permanecem efêmeros no runner e não são enviados como artifact.

## Cruzamento privado

O utilitário local tools/link/private_aot_provider_hash_join.py aceita a entrada privada da Etapa 91 e um ou mais manifestos hash-only:

    python3 tools/link/private_aot_provider_hash_join.py \
      --inventory /caminho/privado/RELATORIO_ETAPA91_ENTRADA_PROVEDORES_PRIVADO.json \
      --provider-manifest /caminho/privado/openorbis-v054-symbol-hashes.json \
      --provider-manifest /caminho/privado/public-runtime-provider-hashes.json \
      --report /caminho/privado/Etapa98_hash_join_agregado.json

O relatório local contém apenas contagens agregadas por classe e módulo consumidor. Não contém nomes, hashes individuais dos símbolos privados, caminhos de provedores ou IDs de objetos consumidores. Mantenha a entrada e o relatório no ambiente privado.

## O que um PASS significa — e o que não significa

- Confirma que os objetos públicos fixados foram compilados para o target PS4 e que o manifesto hash-only foi gerado integralmente.
- Uma correspondência SHA-256 exata indica apenas um candidato de definição por nome.
- Definições múltiplas continuam ambíguas; nenhum provider é selecionado automaticamente.
- Não valida ABI, versão, relocation, convenção de chamada, layout de tipos, ordem de bibliotecas ou dependências transitivas.
- Não realiza link relocável conjunto ou link executável, não cria EBOOT/PKG e não testa instalação, boot, GPU ou gameplay no PS4.

A Etapa 98 é uma triagem de provedores, não uma autorização de link. A revisão ABI fail-closed da Etapa 97 continua obrigatória.
