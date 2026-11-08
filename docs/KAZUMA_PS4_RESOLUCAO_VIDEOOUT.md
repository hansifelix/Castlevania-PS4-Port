# Ponte PS4: callbacks reais de resolução (11/2026)

Foi implementado em `src/ps4/castlevania_resolution.cpp` um provedor de **três**
callbacks AOT, com assinaturas C++ iguais às usadas no upstream fixado:
`nx_castlevania_render_resolution`, `nx_castlevania_framebuffer_resolution`
e `nx_castlevania_depth_resolution`.

A configuração do tamanho nativo **não tem valor padrão**. A integração real
de SceVideoOut deve chamar `kazuma::ps4::video::configure_native(w,h)`
**depois** de descobrir a dimensão de saída efetiva; tamanhos não 16:9 ou
fora de 640x360 a 3840x2160 são rejeitados. O render pode selecionar uma
dimensão menor de mesmo formato. Antes da inicialização, os callbacks chamam
`nx::unimpl` para falhar explicitamente, em vez de mascarar o erro.

## Validação privada (sem publicar arquivos de jogo)

Compilação host Clang C++20 com header de CPU sintético e testes das
convenções x0/x1/x2: PASS. Ligação `ld.lld -m elf_x86_64 -r` do objeto
compilado aos **1.916 códigos AOT + três tabelas + loader/memória**: PASS.
Os três símbolos correspondentes deixam a lista de indefinidos.
A contagem total de nomes externos distintos cai de 119 para 116,
sob essa configuração de link **relocável**.

A ABI final OpenOrbis, a ligação de `configure_native` com o VideoOut,
os demais 10 callbacks gráficos, `STG`, `SVE MOV`, runtime/NVN e o link
**estrito executável** ainda não foram concluídos.

**Não é eboot.bin, PKG, boot PS4 nem gameplay.** Não publicar ELF nem
objetos de jogo no GitHub.
