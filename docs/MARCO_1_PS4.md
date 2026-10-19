# Marco 1 — compilar um executável básico para PS4

Este teste usa uma versão publicada do SDK **OpenOrbis v0.5.4** para transformar o arquivo `ps4_hello/main.cpp` em um `eboot.bin` experimental (sem jogo). É um passo necessário, **mas não suficiente**, para criar um PKG executável.

- A compilação será feita no GitHub Actions após o envio da branch (não usa o Galaxy A73 para compilar).
- **Ainda não há PKG ou tela gráfica**; se funcionar no console, o código escreve mensagem no log e fica num laço de espera.
- O teste não usa o emulador Switch nem realiza a recompilação do Castlevania.
- O artefato `eboot.bin` é parte de um aplicativo PS4, não um aplicativo pronto para instalar isoladamente.
- Se a etapa de compilação falhar, leia os registros da etapa vermelha no GitHub Actions. A falha pode ser de versão/infraestrutura, não do jogo.
- A dependência externa SDK pesa ~159 MB compactada. O download acontece no runner GitHub, não no seu celular.

## Fontes técnicas

- https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain
- https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain/blob/master/samples/hello_world/Makefile
- https://github.com/iHaiDeeZ/SMW/blob/main/docs/BUILDING.md

## Próximo marco

Somente depois do `eboot.bin` compilar, criar PKG mínimo com identificador de TESTE, ícone próprio e logs; testar o PKG no PS4. **Não usar o título de Castlevania ou os arquivos comerciais nessa fase.**
