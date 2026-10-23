# KAZUMA PORT GAMES BR — ETAPA 51: memoria isolada no PS4

**Objetivo:** testar no hardware as funcoes `nx::plat::reserve`, `commit` e `decommit` implementadas na Etapa 50, usando apenas memoria do proprio processo de homebrew.

## Experimento

1. Consulta `sysconf(_SC_PAGESIZE)` e recusa paginas fora de 4–64 KiB.
2. O sistema escolhe uma pagina livre via `mmap(nullptr)`, que e imediatamente liberada. O adaptador tenta reservar **exatamente** essa pagina usando apenas a direcao como *hint* (sem MAP_FIXED).
3. Se houve reserva e `commit`, escreve dois bytes dentro da pagina, valida leitura e chama `decommit` **sem tentar ler depois** (evita fault proposital).
4. Libera o mapeamento com `munmap` e tenta reservar **somente uma pagina** em cada um dos enderecos-base publicos `0x4000000000` (main), `0x4010000000` (sdk), `0x4020000000` (subsdk0), reportando aceite/recusa. Nao testa regioes comerciais grandes, nem carrega modules AOT.
5. Abre a interface Kazuma, com indicador dos resultados e Klog `KAZUMA51:`.

**Limites:** sucesso num teste de 1 pagina **NAO** garante que um modulo inteiro possa ser mapeado, nem inicializa o motor ou a GPU do jogo. Um `DECOMMIT=CHAMADO` nao comprova que protecao foi alterada (API retorna void). O sistema pode recusar enderecos; isso deve ser tratado como falha segura, nao como autorizacao para usar MAP_FIXED.

Esta etapa gera um **PKG experimental de homebrew separado**, SOMENTE se a compilacao no GitHub Actions passar. Nao executa scripts no console de maneira automatica e NAO inclui arquivos de jogos, ROMs, NSPs, saves ou firmware.

## Antes de instalar

- Salvar o progresso dos jogos e fechar aplicativos.
- Usar no PS4 com GoldHEN somente apos inspecionar os checks e baixar artefato do workflow aprovado.
- Ativar Klog Server; o registro deve iniciar com `KAZUMA51: BOOT HOMEBREW`.
- Se travar, encerrar pelo menu PS ou reiniciar normalmente, sem repetir indefinidamente.

## Proximo trabalho

Depois, avaliar se os enderecos-base podem servir para construir mapas maiores sem colisoes; faltam tambem modulos AOT privados derivados de copia compativel, threads, audio e backend de video NVN/GPU. Nao subir dados comerciais ao GitHub publico.
