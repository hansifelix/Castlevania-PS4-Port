# Kazuma Port Games BR — Etapa 9: mapear lacunas do runtime original

## Base confirmada
O merge da etapa 8 registrou 110 simbolos indefinidos nos sete objetos publicos, sendo 84 com nomes correspondentes em bibliotecas estaticas `.a` do OpenOrbis v0.5.4 e 26 sem correspondencia nos `.a` analisados. Correspondencia de nome nao garante link nem compatibilidade de ABI.

## Experimento
- Reproduzir offline a compilacao dos sete objetos publicos, sem dados do jogo.
- Reproduzir a auditoria da etapa 8 para evitar numeros fixados sem teste.
- Demanglar os 26 simbolos restantes com `c++filt` e classificar por tipo: `nx::plat`, runtime `nx`, TLS, suporte C++ e C.
- Procurar **ocorrencias textuais** de identificadores na revisao publica fixa. Isso NAO confirma definicoes nem que o codigo serve para PS4.
- Publicar somente documentos `.md`, `.json`, `.tsv` e logs.

## Proxima decisao tecnica
Inspecionar manualmente interfaces `nx::plat`, ponto de entrada e bibliotecas de plataforma, e avaliar se um programa homebrew minimo **independente de jogo** pode ser linkado e executado no PS4. Nao saltar diretamente para `eboot.bin` do jogo ou PKG de Castlevania.

Nao implica port funcional, compatibilidade de arquitetura de executaveis comerciais nem conclusao do desenvolvimento.
