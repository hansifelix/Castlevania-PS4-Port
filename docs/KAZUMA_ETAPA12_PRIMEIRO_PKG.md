# Kazuma Port Games BR — Etapa 12 (prova de conceito gráfica)

## Escopo

Preparar **um homebrew independente** com tela "KAZUMA PORT GAMES BR — HOMEBREW TEST 01" e tentar empacota-lo em PKG a partir do GitHub Actions. O app nao incorpora nenhuma rotina, dado, asset, APK, NSP, NCA ou biblioteca proprietaria do Castlevania.

A rotina de video adapta a interface `Scene2D` do projeto publico **OpenOrbis-PS4-Toolchain**, revisao fixa `0a1aaf9dd4a92695538bdeb09fb056d06dd11725` (GPL-3.0, ver LICENSE upstream). O código da tela, ícone e scripts desta etapa ficam disponíveis no repositório Kazuma. A tela desenha sua própria fonte bitmap; não usa fontes externas.

Versoes dependentes: OpenOrbis Toolchain v0.5.4 (SHA256 fixo); OpenOrbis/create-fself revisao `f2da6229684ce320f673c06fceac9c218f621788`.

## O que os testes demonstram

- `clang++` compila fontes publicas C++ para ABI de PS4;
- `ld.lld` tenta ligar objetos com `crt1.o`, libc, libc++, kernel e SceVideoOut;
- `create-fself` tenta converter ELF em `eboot.bin`;
- `PkgTool.Core` e `create-gp4` tentam gerar pacote; a prova ainda e **offline**;
- logs + hashes sao publicados mesmo em falha; PKG de teste e publicado em artefato **somente se passar**.

## Teste no console — somente apos analisar checks

Se o build gerar PKG integro, revisar o `resumo.json`, titulo e conteudo. A etapa de instalacao e execucao depende de aceitacao separada pelo proprietario do PS4. O pacote, se gerado, usa o Title ID `BREW91234`, pensado para uso exclusivo como teste; conferir se nao existe aplicativo com esse ID instalado. Nunca instalar durante uma atualizacao do sistema, nem substituir dados salvos. Fechar pelo Menu PS.

**Possiveis resultados:**

- Pacote nem compila → inspecionar erros no workflow e corrigir antes de testar console;
- PKG gerado, mas nao instala → revisar metadados/empacotador, nao atualizar firmware;
- Instala, mas falha ao iniciar → investigar importacoes/libSceVideoOut e runtime; nao prova grafico;
- Exibe tela Kazuma → confirma execução de app independente e interface de video; **nao confirma port do jogo**.

Um check verde nao e prova de execucao no hardware. Nao acessar arquivos de sistema, nem tentar instalar APK/NSP no PS4.
