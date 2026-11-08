# Operação Castlevania PS4 — integração real do VideoOut com os 13 callbacks

Continuando o link conjunto da PR #111, esta rodada combina de uma vez
**dez arquivos de implementação reais**, sem imagens, ROMs ou objetos comerciais:

1. Oito fontes PS4 dos **13 callbacks nx_castlevania_***.
2. `src/ps4/castlevania_game_ps4.cpp` com `nx::game::after_init()`, que
   consulta `nx::plat::screen_size` antes de entrar em `nnMain`.
3. `tools/etapa74/platform_ps4_display.cpp`, com chamadas
   `sceVideoOutOpen`, `sceVideoOutGetResolutionStatus` e
   `sceVideoOutClose` do SDK PS4.

O GitHub Actions usa OpenOrbis v0.5.4, Clang 18 e interfaces MIT upstream
fixadas em `4043f21bb4f656d34cd17ba070238c7728d00631`. Compila
os dez arquivos para `x86_64-pc-freebsd12-elf` e faz **um único link
relocável** `ld.lld -r` de todos. `video_callback_closure.py
--require-videoout` exige que os 13 callbacks estejam presentes, que
`nx::game::after_init` e `nx::plat::screen_size` estejam definidos e
não indefinidos, que os provedores `kazuma::ps4::video::*` estejam
resolvidos e que os três imports `sceVideoOut*` permaneçam visíveis
como **referências externas reais** — sem implementações falsas.

Artefatos publicados são somente listas textuais `llvm-nm`, JSON
de auditoria e hashes. A presença desses imports não prova que o linker
executável conseguirá vinculá-los a bibliotecas definitivas.

**Escopo de PASS:** compatibilidade e referências de **toda a camada
pública de inicialização de vídeo** em um objeto ELF relocável. Isso não
prova apresentação de frames ou gerenciamento dos estados de suspensão
do PS4. As implementações atuais de `nx::game::renderer_start` e
`first_frame` permanecem sem renderização real; NVN, serviços runtime,
SVE/STG, AOT privado de 1.916 objetos, link estrito, eboot e PKG
continuam pendentes. Não chamar esse resultado de port jogável.
