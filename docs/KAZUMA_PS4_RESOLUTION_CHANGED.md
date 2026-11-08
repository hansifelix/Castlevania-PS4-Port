# Castlevania PS4 — callback real de troca de resolução

Implementação adaptada do MIT público `games/castlevania/video_options.cpp`
(pinned upstream `4043f21bb4f656d34cd17ba070238c7728d00631`).

### Propriedades implementadas
- `nx_castlevania_resolution_changed(nx::CPU&, void (*)(nx::CPU&))`
  preserva a invocação original.
- Obtém índice selecionado pelo método virtual **do próprio jogo**,
  lê tabela gerenciada a partir do endereço específico desta revisão e
  rejeita índices/contagens/medidas inválidas.
- `kazuma::ps4::video::select_render` altera **apenas** a resolução de
  renderização interna (exige `VideoOut` configurado).
- Chama o setter **do jogo** em `NX_BASE+0x4e00a50`, com ABI e flags originais,
  usando modo 1 (tela cheia desktop) no PS4. Não tenta redimensionar
  uma janela inexistente: o VideoOut físico mantém a resolução nativa.

### Verificações
CTest host usa exclusivamente fixture sintética para o ponteiro
`NX_BASE+0x6be3ec8`, setter/método virtuais e arrays.
Workflow de ABI compila os dois arquivos reais (callback e ponte de resolução)
com headers upstream e OpenOrbis 0.5.4/Clang18 e executa
`ld.lld -r`, exigindo que `select_render` seja resolvido pelo provider real.

### Limitações
Não altera as superfícies de NVN e não prova que um novo frame é apresentado.
A união relocável **não** equivale a link executável PS4; a validação com
os 1.916 objetos AOT privados ainda é necessária. Nenhum conteúdo comercial,
ROM, PKG ou eboot é publicado.
