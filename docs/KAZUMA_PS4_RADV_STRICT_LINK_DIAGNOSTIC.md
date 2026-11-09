# Operação Castlevania PS4 — diagnóstico estrito da fatia NVN/RADV (Etapa 64)

## Resultado da primeira tentativa

A execução pública da integração NVN + vkloader + Mesa/RADV real
(Actions #42515971861) passou no link relocável parcial. Os três
provedores ICD reais foram definidos, mas o relatório ainda registrou
423 nomes de símbolos indefinidos.

A PR draft #127 executou o linker estrito da fatia GPU isolada
(Actions #42609853444). Resultado observado:

- link relocável NVN/RADV: PASS_PARTIAL_RADV;
- link estrito com OpenOrbis v0.5.4 + libSceGnmDriver: BLOCKED;
- linker exit code 1, limite 100 mensagens, 100 símbolos indefinidos
  reportados, zero bibliotecas ausentes e um aviso de limite de erros;
- tempo do linker: 146 ms;
- saída: /dev/null; nenhum ELF salvo, nenhum EBOOT/PKG e zero bytes
  escritos no Google Drive.

Os primeiros símbolos reportados foram nx::game::kInfo, nx::log,
nx::nvn::ReplayScope (construtor/destrutor), nx::nvn::astc_native,
nx::nvn::async_gpu, nx::nvn::creation_log e nx::nvn::debug_dump_add.
A experiência compilou apenas seis objetos NVN/ponte/vkloader mais
o arquivo RADV e zlib. Ela não incluiu o restante do runtime público.
Assim, esses primeiros erros apontam para provedores de runtime
ausentes nessa fatia, não para uma biblioteca RADV comprovadamente
ausente. Não classificar isso como falha do port completo.

## Próximo passo técnico

Inventariar todos os símbolos indefinidos por origem e, em seguida,
combinar a fatia GPU com o conjunto público de runtime/adaptadores PS4
antes de uma nova tentativa de link estrito. Não usar stubs no-op,
não incluir AOT privado no repositório público e não mascarar um
resultado BLOCKED como CI verde.

## Limites

O teste não inclui os sete AOT privados, os 87 objetos completos do
runtime, RomFS, SPIR-V de Castlevania ou dados comerciais. Não executa
Vulkan, WSI ou VideoOut no PS4. Mesmo PASS_DRYRUN seria apenas a lista
exata de objetos submetida ao linker, sem ELF salvo ou prova de boot.
