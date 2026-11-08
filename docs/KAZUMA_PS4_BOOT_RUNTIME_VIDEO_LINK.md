# Castlevania PS4: integração pública do boot, loader, memória e vídeo

Este teste avança além da PR #112: não basta ligar callbacks isolados.
Um único workflow com OpenOrbis v0.5.4 e Clang 18 compila **15 fontes C++**
do runtime e da adaptação PS4 em um único `ld.lld -r` ELF relocável:

- upstream MIT fixado em `4043f21bb4f656d34cd17ba070238c7728d00631`:
  `runtime/src/main.cpp` (`nx::boot`), `loader.cpp` (`nx::call`,
  `nx::unimpl`), `memory.cpp` (`nx::memory_init`, `nx::commit`, `nx::vm_set`);
- Kazuma: `platform_ps4_memory.cpp` (reservar/commitar/decommitar),
  `linked_modules_castlevania.cpp` (registro triplo), dez fontes da pilha
  de vídeo PS4 com 13 callbacks, `nx::game::after_init` e SceVideoOut.

O link parcial exige que os provedores fundamentais estejam **definidos,
não duplicados e não indefinidos**. Também exige imports reais
`sceVideoOutOpen`, `sceVideoOutGetResolutionStatus` e
`sceVideoOutClose`, sem falsificar essas APIs do console.

Importante: os símbolos privados `nx_module_main`, `nx_module_sdk` e
`nx_module_subsdk0` **devem continuar indefinidos neste teste público**.
As tabelas reais AOT foram mantidas fora do repositório e do CI, como
nas etapas anteriores. O gate falha se aparecerem definições fictícias.

O workflow publica apenas inventário de símbolos, hashes e JSON.
**PASS não significa link estrito**, nem resolução total de serviços,
nem GPU NVN, nem geração de EBOOT/PKG. Nenhuma execução do jogo.

O próximo avanço decisivo, em ambiente privado do usuário, é integrar
as três tabelas verdadeiras e os 1.916 objetos no link final, diagnosticar
as dependências transitivas C++/plataforma restantes e avançar sobre
semântica STG/SVE e o renderer.
