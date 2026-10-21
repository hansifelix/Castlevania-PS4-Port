# Kazuma Port Games BR — Etapa 11: OELF e fSELF homebrew minimo (SEM JOGO)

## Ponto de partida

A PR #18 comprovou que um arquivo ELF x86-64 `ET_DYN` minimo, baseado apenas
em codigo C independente, pode ser ligado *offline* com `crt1.o`, `libc` e
`libkernel` do OpenOrbis v0.5.4.

## Objetivo do novo experimento

Repetir o mesmo link, e usar a ferramenta publica [OpenOrbis/create-fself]
(https://github.com/OpenOrbis/create-fself) numa revisao fixa para tentar:

1. Criar um **OELF** intermediario.
2. Empacota-lo em um **fSELF** temporario de homebrew, denominado `eboot.bin`.
3. Analisar a presenca dos cabecalhos correspondentes, tamanhos e SHA256.

Nenhum dado do jogo, porta de Switch, APK, NSP, NCA, asset ou arquivo
comercial participa deste experimento. A unica fonte de codigo C executavel
provem do teste anterior: `tools/etapa10/minimo_homebrew.c`.

## Procedimento

- O runner faz download do OpenOrbis v0.5.4 com checksum SHA256 fixo.
- Clona `OpenOrbis/create-fself` na revisao fixa
  `f2da6229684ce320f673c06fceac9c218f621788`.
- Compila `create-fself` localmente em Go, usando `go-linux.mod` do proprio
  repositorio (sem uso de binario converter nao auditado).
- Compila e liga novamente o ELF minimo como na etapa 10.
- Faz a conversao com `create-fself -in ... -out ... -eboot ...`.
- Inspeciona os cabecalhos e guarda **somente logs, hashes e JSON**.
- Executaveis, OELFs e fSELFs temporarios sao apagados no fim do job.

## Leitura correta do resultado

* **Verde**: conversao de formato e verificacao de cabecalho foram concluídas
  offline. **Nao confirma** instalacao, inicializacao nem execucao no PS4.
* **Vermelho**: indicio concreto de falha de compilacao/conversao ou formato;
  verificar os logs completos antes de propor correcoes.

Uma conversao bem-sucedida nao resolve as 26 referencias sem equivalencia
identificadas na Etapa 9. Nenhuma etapa aqui testa renderizacao, audio,
controles, motor do jogo, arquivos comerciais, assinatura oficial ou PKG.
Proximo passo possivel, apenas depois de revisar o resultado: elaborar um
pacote homebrew *separado*, seguro e reversivel para validacao no console.
