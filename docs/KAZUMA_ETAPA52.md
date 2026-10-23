# Kazuma Port Games BR — Etapa 52

**Auditoria de endereços públicos; nenhuma alteração ao port do jogo, nenhum PKG nesta etapa.**

A Etapa 51 validou apenas três reservas de 16 KiB (uma página por base) no PS4. O upstream exige regiões muito maiores. A Etapa 52 audita um *piso* baseado nos `image_bytes` do manifesto público fixado em `4043f21bb4f656d34cd17ba070238c7728d00631` e o mapa host público do runtime. **Não confundir `image_bytes` com `bss + bss_size` reais.**

Saídas: `relatorios/etapa52/LEIA_PRIMEIRO.md` e `MAPA_MEMORIA.json`, publicados como artefato no GitHub Actions. A branch não inclui ROMs, NSP, APK, ExeFS, RomFS nem módulos AOT privados.

O próximo passo após analisar o relatório é obter **apenas os parâmetros técnicos necessários** da recompilação feita localmente a partir de uma cópia compatível; nunca enviá-los ao repositório público se implicarem código ou dados comerciais. Só depois de validar os intervalos planejar um novo microteste seguro no PS4.

**Não instalar nenhum PKG por causa desta etapa.**
