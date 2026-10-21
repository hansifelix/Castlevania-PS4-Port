# Kazuma Port Games BR — Etapa 10: primeiro link ELF homebrew independente

## Objetivo
Comprovar ou descartar uma ligacao **offline** minima entre codigo C novo, `crt1.o`, libc e libkernel do OpenOrbis v0.5.4. Nenhum componente do Castlevania, assets, NSP, NCA, APK ou executavel comercial e usado. O experimento usa o mesmo alvo `x86_64-pc-freebsd12-elf` das etapas anteriores.

## Procedimento
1. Baixar OpenOrbis v0.5.4, validar SHA-256 fixo.
2. Compilar `minimo_homebrew.c` para objeto ET_REL x86-64.
3. Tentar link como ELF PIE usando `link.x`, `crt1.o`, `-lc`, `-lkernel`.
4. Se falhar, relatar erro sem mascarar simbolos indefinidos.
5. Se passar, auditar cabecalho ELF, ponto de entrada, PT_LOAD, hash e diagnosticos.
6. Descartar objetos e ELF temporarios e publicar **somente texto e JSON**.

## Interpretacao
- **Check verde**: compilacao, ligacao e validacao estrutural ELF offline concluiram. NAO e prova de binario OELF/FSELF, eboot, PKG, carregamento ou execucao no PS4.
- **Check vermelho**: evidencia concreta de obstaculo no linker/SDK; revisar os logs antes de alterar parametros.
- **Proximo passo, apos relatorio**: avaliar se vale gerar e testar um homebrew independente no PS4, com autorizacao e procedimento separado. Isso nao resolve automaticamente as 26 lacunas da etapa 9, audio, grafico, sistema ou o jogo.

Nao usar hacks de linker para ignorar undefined nem afirmar que a arquitetura do runtime basta para portar o jogo. A compatibilidade do software original e uma questao separada.
