# Kazuma Port Games BR — Etapa 48 — Primeiro diagnóstico de BOOT REAL

**Meta:** incorporar o `runtime/src/main.cpp` do runtime público de Castlevania
na tentativa de ligação OpenOrbis e descobrir o bloqueio real de `nx::boot()`.

Esta etapa troca o adaptador de relógio antigo pelo que passou no PS4 na Etapa 47,
compila `nx::boot()` e um `main()` que realmente o chama, gera um objeto
relocável e tenta o link **estrito** com bibliotecas OpenOrbis.

Não inclui os módulos comerciais recompilados `main/sdk/subsdk0`, dados de
ExeFS/RomFS nem assets. **87 componentes de runtime não são o jogo completo.**
Um erro `nx::linked_modules`, `nx_module_main`, `nx::game::...` é evidência
objetiva de que ainda falta a saída de recompilação do jogo, além das APIs
PS4 pendentes. O sucesso dos checks significa apenas que os diagnósticos foram
executados. Não há PKG e nenhum teste será instalado no PS4 nesta etapa.

**Ler nos artifacts do GitHub Actions:** `relatorios/etapa48/LEIA_PRIMEIRO.txt`,
`RESUMO.json`, `COMPILAR_BOOT.log`, `LINK_ESTRITO_BOOT.log` e grupos de símbolos.

Se ficar tudo verde, **não concluir que o jogo abre**. Etapa posterior:
tratar APIs nativas, reconstrução dos módulos AOT a partir dos arquivos do
proprietário em ambiente privado, e pipeline de renderização, áudio e entrada.
Não subir NSP, APK, ExeFS, RomFS, chaves ou binários do jogo ao repositório público.
