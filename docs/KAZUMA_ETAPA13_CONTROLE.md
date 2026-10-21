# Kazuma Port Games BR — Etapa 13 — Controle + memoria (homebrew Test 02)

A Etapa 12, PR #20, foi incorporada a main e seu aplicativo **Test 01** teve inicializacao e video observados no PS4 do desenvolvedor. Essa prova NAO confirma o novo Test 02.

## Proposta de hardware
- Manter o helper de video e o empacotamento da etapa 12 v1.01.
- Usar `libScePad` e `libSceUserService` dos stubs OpenOrbis.
- `X` alterna a cor do indicador; `QUADRADO` refaz verificacao de 64 KiB de memoria do aplicativo; `O` encerra o app.
- A tela mostra se o controle foi detectado, ultimo botao e resultado do teste de memoria.
- PS sempre pode abrir menu do sistema; caso nao detecte controle, usar PS para sair.
- Novo Title ID `BREW91235` e Content ID `IV0000-BREW91235_00-KAZUMAPADTEST000` para NAO substituir o Test 01 (`BREW91234`).

## Resultado esperado
Passar na CI comprova apenas compilacao + ligacao + conversao + PKG. No PS4, se o app iniciar, premir X deve mudar o indicador, QUADRADO deve mostrar 'MEMORIA 64KB: OK' se o teste passar e O deve fechar o app. Se falhar, fornecer video/erro, sem tentar atualizar firmware, reinicializar ou repetir instalacoes.

## Limites
Somente codigo homebrew independente. Nada do Castlevania (jogo/asset/ROM/NSP/APK) nesta etapa. Executar no hardware so apos checks, auditoria e escolha do usuario. Nao fazer merge antes de revisar o relatorio. Evitar perder save ou instalar sobre outro Title ID. O helper grafico OpenOrbis e GPL-3.0; manter licenca e credito ao redistribuir.
