# Kazuma Port Games BR — Etapa 44

## Objetivo técnico

A Etapa 43 confirmou que o SDK consegue criar um ELF mínimo. A Etapa 42 encontrou **33 símbolos distintos no log** da tentativa de ligação do runtime, incluindo `main`, `nx::game::kInfo`, `nx::linked_modules()`, 27 APIs `nx::plat`, e `__cxa_thread_atexit_impl`. Isso NÃO equivale a 33 implementações únicas que podem ser feitas diretamente.

Nesta etapa, testaremos a ligação estrita de **oito APIs já implementadas** das Etapas 38 e 40, junto de um `main` de diagnóstico próprio. Isso isola problemas C++/ABI e de bibliotecas de problemas de recursos de jogo e apresentação gráfica, sem fingir integrar a aplicação comercial.

A auditoria deve produzir `relatorios/etapa44/LEIA_PRIMEIRO.txt` e `LINK.log`. Um check verde significa somente que a auditoria concluiu; `ELF_INTERMEDIARIO` significa que existe ELF offline desse teste, nunca PKG/eboot nem execução real PS4.

## Portabilidade e atribuição

Sem NSP, APK, ROM, shaders ou recursos comerciais. `smoke_real.cpp` é um pequeno programa independente; utiliza APIs reais do adaptador já presente, com leitura opcional de arquivo de sistema, sem criar diretorios ou tocar saves. NÃO executar o teste como jogo. Não substituir a implementação de APIs do jogo por stubs para forçar checks verdes.

## Roadmap depois

- Se a ligação falhar: priorizar os símbolos de biblioteca/ABI identificados, usando providers reais.
- Se a ligação funcionar: produzir build de teste para PS4 com mensagens de diagnóstico, revisando compatibilidade de EBOOT/PKG antes de qualquer instalação.
- Manter a marca Kazuma Port Games BR discreta e a arte original quando houver interface funcional (decisão registrada em `docs/KAZUMA_BRANDING_PORT_PS4.md`).
