# Kazuma Port Games BR — Etapa 45 — Teste hardware de 8 APIs

Este pacote tenta gerar um PKG **homebrew independente**, sem codigo ou dados comerciais de Castlevania. Compilar o PKG nao comprova o funcionamento no PS4.

## Na TV (se iniciar corretamente)
- Logo textual *pequena* no alto: `KAZUMA PORT GAMES BR`.
- Status `RELOGIO`: monotonic_ns + sleep_ns.
- Status `ARQUIVO`: abre fixture sintetica `kazuma45.dat` em /app0, testa ftell64, fseek64, read_at sem alterar o offset de FILE*.
- Status `PASTA INVALIDA`: make_dirs("") rejeita caminho vazio; **nao grava** pastas nem dados.
- Status `CONTROLE`: leitura da libScePad; X confirma; QUADRADO repete diagnósticos; PS abre o menu de encerramento.
- Logs `KAZUMA45: ...` em stdout, potencialmente visiveis no Klog Server GoldHEN.

## Cuidados
- Nenhuma API escreve ou altera saves.
- Marca e tela propria de TESTE, NAO interface original de Castlevania.
- Nao instalar se GitHub Actions estiver vermelho; se o build ficar verde, conferir artefatos e testar voluntariamente.
- Se causar travamento ou erro do PS4, encerrar pelo menu PS; nao ficar repetindo sem analisar klog.
- O teste nao integra 87 objetos do runtime nem renderizacao do jogo comercial.
