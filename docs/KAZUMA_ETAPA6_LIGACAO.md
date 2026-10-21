# Kazuma Port Games BR — Etapa 6: auditoria de ligacao do runtime

## O que estamos comprovando

Partimos da Etapa 5 (`4/4` objetos ELF relocaveis, alvo `x86_64-pc-freebsd12-elf`) e tentamos **reunir os quatro objetos com `ld.lld -r`**. Esta e uma **ligacao parcial relocavel**, nao um link final nem executavel do PS4.

Usamos apenas fontes publicos do upstream SwonDev/cstlvnia-blmont-to-macos na revisao fixa `4043f21bb4f656d34cd17ba070238c7728d00631` e OpenOrbis v0.5.4 com hash verificado.

## O que o workflow documenta

- Recompila os quatro objetos conhecidos e testa `4/4 PASS` com o mesmo script da Etapa 5.
- Audita ELF x86-64 relocavel (`ET_REL`) de cada objeto.
- Reune os objetos numa unica unidade ELF relocavel, sem link final.
- Enumera simbolos definidos e ainda indefinidos (dependencias externas), com relatorio em JSON.
- Publica logs mesmo se falhar. Um check verde **nao** indica que as dependencias estao resolvidas.

## O que NAO esta sendo feito

**Nao** estamos recompilando modulos comerciais `main`, `sdk` ou `subsdk0`. Nenhum arquivo APK, NSP, NCA, ROM, chave, audio, video, asset, eboot ou PKG e usado. Nao instala nada no PS4.

**Nao** valida carregamento de memoria, Vulkan/RADV, ligacao com bibliotecas do PS4, inicializacao do runtime, controles, execucao do jogo, estabilidade ou FPS. Nao ha garantia de portabilidade total.

## Proximo passo condicional

Analise do `resumo.json` e de `parcial_indefinidos_legiveis.txt` para classificar referencias e planejar adaptadores PS4 (`nx::plat`, libc++, kernel, gpu). Depois, verificar a possibilidade de uma ligacao final com **codigo publico somente**, separadamente, antes de qualquer PKG.
