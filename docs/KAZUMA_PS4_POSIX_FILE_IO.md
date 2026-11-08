# Operação Castlevania — operações de arquivos POSIX para PS4

O artefato REAL da PR #115 (`42450736859`) deixou entre outras funções
externas `nx::plat::fopen_utf8`, `fseek64`, `ftell64`,
`read_at`; a interface `make_dirs` também precisa ser implementada.

`src/ps4/platform_ps4_file_io.cpp` implementa as cinco com operações
POSIX reais: `fopen`, `fseeko`, `ftello`, `pread`, `mkdir/stat`.
Em particular, `read_at` mantém o cursor `FILE*` intacto, retorna a
quantidade exata realmente lida, repete `EINTR` e usa blocos de 1 MiB.
Não inventa bytes nem retorna sucesso quando faltam diretórios.

O GitHub Actions compila **23 fontes reais** do runtime com
OpenOrbis v0.5.4 e Clang18; faz um único link ELF relocável `ld.lld -r`,
verifica os cinco símbolos por `llvm-nm`, e executa teste host POSIX
para leitura, EOF, cursor, nomes inválidos, idempotência e pastas reais.
O gate legado das PRs #113–115 permanece independente.

**Escopo restrito:** operações POSIX não são equivalente a montar o
SaveData do PS4; `nx::plat::data_root`, `setting`, gerenciamento de
salvamentos e permissões/sandbox do console continuam sem solução
aqui. Ainda não é link executável, EBOOT, PKG ou gameplay. Outros
símbolos libc++, threading e NVN podem continuar indefinidos.
Nenhuma ROM/objeto comercial é incluído.
