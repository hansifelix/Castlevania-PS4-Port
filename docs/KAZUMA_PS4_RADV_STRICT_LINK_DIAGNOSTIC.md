# Operação Castlevania PS4 — diagnóstico estrito da fatia NVN/RADV (Etapa 64)

## Por que esta etapa existe

A execução pública da integração NVN + vkloader + Mesa/RADV real
(Actions #42515971861) terminou com sucesso no **link relocável parcial**.
O gate confirmou os três provedores ICD e a ponte NVN, mas o próprio
relatório registrou **423 nomes de símbolos ainda indefinidos**. Isso não
era um link executável estrito.

## O que o diagnóstico novo faz

No mesmo runner, usando o mesmo objeto combined.o recém-gerado,
executa o linker OpenOrbis v0.5.4 com:

- crt1.o e link.x reais do SDK;
- -lc++, -lc, -lkernel, -lm quando disponível;
- -lSceGnmDriver, biblioteca real do SDK;
- -pie --no-undefined --fatal-warnings;
- saída fixa em /dev/null, sem criar outro ELF no disco.

O limite de diagnóstico é configurável até 100 mensagens. O JSON registra
contagens e até oito exemplos por classe (símbolos indefinidos,
bibliotecas ausentes e outros erros). O linker pode truncar mensagens;
por isso as contagens são do log observado, não uma garantia de inventário
completo.

## Interpretação obrigatória

- BLOCKED / exit 2: o link estrito desta fatia NVN/RADV não fechou.
  O CI deve ficar vermelho; não mascarar a falha como sucesso.
- PASS_DRYRUN: o linker aceitou somente esta lista de objetos e
  bibliotecas, escrevendo em /dev/null. Não há ELF validado, fSELF,
  EBOOT, PKG ou teste de inicialização.
- ERROR: entrada, SDK, ferramenta ou timeout; não tratar como
  erro do runtime do jogo.

Este ensaio não inclui os sete AOT privados, os 87 arquivos do runtime
completo, RomFS, SPIR-V de Castlevania ou qualquer dado comercial. Não
usa Google Drive nem grava arquivos nele. Não executa Vulkan, WSI ou
VideoOut no PS4.

## Próximo bloqueio após o resultado

Se o link falhar, usar os exemplos reais para identificar a biblioteca
OpenOrbis/Mesa correspondente e só então acrescentar dependências
verificadas. Não criar stubs vazios, não declarar o WSI pronto e não
misturar esta fatia pública com os objetos AOT privados do laboratório.
