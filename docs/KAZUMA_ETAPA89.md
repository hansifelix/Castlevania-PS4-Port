# Castlevania PS4 — Etapa 89: loader upstream + AOT real do subsdk0 (07/11/2026)

## Evidência privada desta etapa
- Os 73 objetos de código do `subsdk0` foram recuperados e verificados por SHA-256, a partir dos dez backups privados já existentes (Etapas 83/85).
- O `loader.o` foi compilado **somente de código público** do upstream (`SwonDev/cstlvnia-blmont-to-macos`, commit `4043f21bb4f656d34cd17ba070238c7728d00631`) por **OpenOrbis v0.5.4 + Clang 18** no GitHub Actions. Esse artefato público, sem dados do jogo, foi baixado para um ambiente de trabalho privado.
- A tabela real `table.cpp` do `subsdk0` (14.173 funções) foi recompilada localmente por Clang de host usando **cabeçalhos mínimos de declarações compatíveis** com as estruturas públicas; não confundir este compilador de host com a confirmação anterior (Etapa 87) com OpenOrbis.
- `ld.lld -m elf_x86_64 -r` com **75 objetos** (73 de código + tabela + loader): **PASSOU**, ELF relocável de **61.884.896 bytes**.
- `nm -u` no objeto resultante: **94 símbolos indefinidos**, dos quais 8 pertencem a serviços/núcleo/plataforma `nx`; 4 são `ceil`, `floor`, `fma`, `trunc`; os outros 82 são serviços ABI/C/libc++ ou outras bibliotecas.
- **`nx::call(nx::CPU&, unsigned long)` e `nx::unimpl(nx::CPU&, unsigned long, char const*)` deixaram de aparecer como indefinidos** — são atendidos pelo carregador original, sem stubs falsos.
- O `nx_module_subsdk0` permanece presente no objeto combinado. Nenhum objeto comercial, C++ do jogo, ROM, keys ou código recompilado privado foi enviado ao GitHub.

## Alteração neste PR público
Ajuste no workflow da Etapa 88-B: após compilar e validar as funções do `loader.cpp`, ele guarda um artefato `loader.o` e hash SHA-256 com caminho relativo. Esse arquivo é resultado **somente do projeto upstream público** e pode ser baixado para uma máquina PRIVADA para repetir um link AOT. Os arquivos de jogo continuam fora do CI e de qualquer PR pública.

## Limitações e próximo bloqueio
`ld.lld -r` **não resolve todas as dependências**, e o número de símbolos indefinidos aumenta quando agregamos o loader: isso é normal. Não é o mesmo que link estrito ou um programa PS4 executável. A ligação usou uma tabela compilada com um subconjunto equivalente dos headers em ambiente host; uma reprodução totalmente em OpenOrbis será necessária antes de declarar conformidade integral da ABI.

**Próximo trabalho:** integrar componentes autênticos de memória/serviços/plataforma, resolver libc++/libm no link estrito, estabelecer o registro correto de `main`, `sdk` e `subsdk0`, e só então buscar a primeira inicialização real. NVN→SPIR-V continua uma frente separada, não concluída.

**Estado:** não existe `eboot.bin` nem PKG jogável; gameplay não testado. Crédito do trabalho de adaptação: **Kazuma Traduções**, preservando autoria do jogo original.
