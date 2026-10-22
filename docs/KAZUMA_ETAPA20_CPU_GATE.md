# Kazuma — Etapa 20: primeira porta de compilacao nx::CPU no toolchain PS4

**O que esta fase pretende decidir:** se as declaracoes e helpers elementares de
`nx/cpu.h`, usados por funcoes reescritas em C++ a partir do fluxo AArch64,
podem ser compilados com o SDK OpenOrbis (x86-64) e ligados num ELF basico.

**O que nao pretende decidir:** se o jogo Castlevania roda no PS4, se seu
codigo AArch64 foi recompilado, se o mapa guest fixo cabe no console, ou se
existe backend NVN/Vulkan adequado. O codigo de teste e totalmente sintetico,
nao usa dados do jogo e **nao converte ELF para PKG nem executa no console**.

## Operacao

1. Use apenas GitHub Actions para compilar; nao ha instalacao no PS4.
2. Se o job falhar, consulte `compilar.stderr.txt` ou `link.stderr.txt` no
   artefato de diagnosticos. Nao trate o problema automaticamente como um veto
   definitivo ao port: pode ser ajuste do toolchain, biblioteca ou ABI.
3. Se passar, isso so confirma o subconjunto testado e permite decidir se vale
   um experimento de recompilacao **de codigo ARM64 sintetico**, antes de usar
   qualquer arquivo de jogo.

## Proximos bloqueios independentes

- Mapa de memoria guest fixo e enderecos do carregador original.
- Recompilacao de codigo real e resolucao de imports, possivelmente varios GB
  de objetos e recursos intermediarios.
- APIs de threads, arquivos, serviços, video e audio do runtime.
- Traducao de NVN e shaders para infraestrutura grafica acessivel no PS4.

A quantidade de etapas nao e previsao de dias. Sem atender essas restricoes
nao e possivel prometer o menu do jogo nem anunciar inviabilidade definitiva.
