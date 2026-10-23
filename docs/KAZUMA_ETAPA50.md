# Kazuma Port Games BR — Etapa 50: primeiro adaptador de memória do runtime

Esta etapa testa **3 símbolos reais** exigidos pelo runtime público de
Castlevania: `nx::plat::reserve`, `nx::plat::commit` e `nx::plat::decommit`.

## Limites e segurança

- Não usa `MAP_FIXED`: reserva com endereço solicitado como **dica** ao SO,
  verifica igualdade estrita; se outro endereço for retornado, o desmapeia e falha.
- Mapeamentos existentes nunca são substituídos intencionalmente.
- Consulta o tamanho de página pelo SO, sem presumir 4096 bytes no PS4.
- Só permite `commit/decommit` em regiões cadastradas pelo próprio adaptador.
- `decommit` remove acesso e solicita descarte de páginas; não garante
  devolução física de RAM no PS4.
- `reserve` pode falhar em endereços exigidos pelo jogo; a solução correta pode
  exigir outra API específica da plataforma, sem sobrescrever regiões alheias.
- Testes de leitura/escrita são **somente Linux**, nunca executados no console.
- A memória real do PS4 só será experimentada futuramente com outro homebrew
  restrito e instrumentado. Nesta etapa NÃO há PKG/execução no console.

## Evidências após a PR

Artefato: `kazuma-etapa50-memoria-ps4-analise-sem-pkg`.
Leia `relatorios/etapa50/LEIA_PRIMEIRO.txt`, `RELATORIO.json`, `COMPILACAO.log`,
`LINK_PARCIAL.log` e `LINK_ESTRITO.log`.

**Check verde** prova apenas execução dos diagnósticos. Não demonstra
que `nx::boot()` foi executado, que endereços do jogo podem ser reservados,
que ELF final foi gerado ou que Castlevania possa renderizar.

## Depois

A prioridade será medir **quais endereços exatos são usados pelo runtime**, se
são livres e se o PS4 pode reservá-los sem conflitos. Em paralelo, falta a
recompilação AOT privada da cópia compatível do jogo (conteúdo 1.1.0), threads,
GPU, áudio e entrada. Não subir NSP/APK/ExeFS/RomFS, assets ou módulos
recompilados de obra comercial a repositório público.
