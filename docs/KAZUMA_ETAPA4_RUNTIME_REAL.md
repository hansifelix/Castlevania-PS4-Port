# Kazuma Port Games — Etapa 4: testar o runtime ORIGINAL de Castlevania

Este pull request executa no GitHub Actions, em Ubuntu x86-64, **código C++ real do runtime público** do projeto de recompilação `SwonDev/cstlvnia-blmont-to-macos`, sem o código comercial de Castlevania e sem dados proprietários.

Repositório de referência: https://github.com/SwonDev/cstlvnia-blmont-to-macos

Revisão fixada para reprodução: `4043f21bb4f656d34cd17ba070238c7728d00631`.

Com `-DNX_BUILD_GAME=OFF -DNX_TESTS=ON`, o workflow compila e executa os quatro alvos independentes do código original:

- `time_service_test` — serviço de relógio do runtime.
- `thread_control_test` — controle de threads do runtime.
- `audio_out_test` — contratos de áudio do runtime.
- `weak_import_test` — resolução de importações opcionais do loader.

## O que esse resultado significa

- Sucesso: os alvos selecionados do runtime original foram construídos/testados em Linux x86-64 com essa revisão. É mais relevante que testes de adaptadores escritos isoladamente.
- Falha: os relatórios mostram se houve problema de configuração, dependência, compilação ou teste. A falha **não** demonstra que o port é inviável.

## O que este PR NÃO faz

- Não recompila nenhum módulo comercial do jogo (`main`, `sdk`, `subsdk0`).
- Não instala nada no PS4, não cria PKG/eboot, não valida Vulkan, RADV, memória de convidado nem inicialização.
- Não prova que Castlevania abrirá no PS4. E **não** testa o desempenho do console.
- Não copia o runtime público para dentro de nosso repositório. Os testes obtêm uma revisão pública pinada e executam-na no CI.

## Próximos critérios reais

1. Obter os quatro testes originais verdes e guardar o artefato com o SHA.
2. Mapear dependências desses serviços com `nx::plat` e os adaptadores PS4 necessários.
3. Separadamente, corrigir a cadeia de build `eboot.bin`/PKG do laboratório comparando com a v1.3.2 conhecida por iniciar.
4. Somente após a segurança do console ser avaliada, retomar testes PS4 com logs e hipóteses controladas.

**Privacidade:** não envie NSP, APK, NSO, chaves ou materiais do jogo ao GitHub público.
