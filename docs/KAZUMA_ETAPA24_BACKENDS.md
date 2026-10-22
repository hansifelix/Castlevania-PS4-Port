# Etapa 24 — escolha provisoria de backend Vulkan PS4

A PR #31 encerrou o diagnostico de divergencia entre o runtime Vulkan 1.3 e o backend OpenGNM com header declarando 1.1.0. Essa divergencia **nao e veto** ao port.

Nesta etapa sao comparadas duas alternativas com codigo publico e commits fixos: `orbis-ports/mesa-ps4` e `PS4-OpenGNM/vulkan-ps4`. O teste verifica o ramo RADV para GFX7, a existencia de codigo WSI Orbis/VideoOut, as dependencias de compilacao, e a declaracao de API/exports no OpenGNM.

**Nao compila Mesa, nao produz ELF/PKG, nao utiliza codigo nem assets comerciais e nao testa hardware PS4.** A classificacao de Mesa como candidato prioritario e apenas uma decisao para escolher o proximo teste, nunca prova de compatibilidade com a GPU ou o NVN do jogo.

Se o workflow passar, ler `relatorios/etapa24/RELATORIO.md` e `resultado.json` antes de merge. O proximo experimento justificavel e um build isolado do candidato (fontes e dependencias fixadas), seguido eventualmente de um smoke test de Vulkan na GPU do PS4 antes de testar o runtime. Memoria do jogo, loader e servicos continuam pendentes.
