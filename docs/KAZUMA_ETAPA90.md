# Castlevania PS4 — Etapa 90: descobrir provedores dos 94 símbolos indefinidos

## Por que esta etapa existe

A Etapa 89 comprovou link `ld.lld -r` de 75 objetos privados (73 códigos,
`table.cpp`, `loader.cpp`) e resolução real de `nx::call/unimpl`, mas
restam **94 símbolos indefinidos** (8 relacionados a serviços `nx`,
4 `ceil/floor/fma/trunc` e 82 C/C++/ABI/outras dependências).
O objetivo não é diminuir o contador escondendo os símbolos: é identificar
qual componente legítimo realmente oferece cada definição.

## Instrumento implementado

`tools/etapa90/symbol_providers.py` compara os símbolos indefinidos
de um objeto ELF com as definições globais de objetos/bibliotecas candidatos,
**por nome exato**, preservando mangling e versões ELF.
Retorna `candidate` ou `missing` para cada símbolo, categoriza-os para triagem
(`nx_runtime`, `platform`, `libm`, `cxx_abi`, `c_or_other`) e gera JSON.

Os símbolos podem vir de `llvm-nm` ou `nm`, sem demangle (`-C`) para
garantir que o nome realmente usado pelo linker é o mesmo.
**O relatório é apenas uma lista de candidatos, não um link estrito aprovado.**
Mesmo um nome exatamente igual pode ter problemas de ABI, relocação ou
dependências transitivas: essas são verificadas somente pelo linker real.

## Como rodar PRIVADAMENTE (em PC/Colab, sem publicar objetos do jogo)

```bash
llvm-nm --undefined-only -g combined_aot_loader.o > need.nm
llvm-nm --defined-only -g loader.o > loader.nm
llvm-nm --defined-only -g outro_provider.o > provider.nm
python3 tools/etapa90/symbol_providers.py \
    --undefined need.nm \
    --defined loader=loader.nm \
    --defined outro=provider.nm \
    --json ../relatorio_privado.json \
    --fail-on-missing
```

**Cuidado:** `nm` em arquivos `.a` de bibliotecas grandes pode incluir
candidatos que nunca serão extraídos automaticamente em ordem de link;
o próximo passo depois da análise é link estrito OpenOrbis, com bibliotecas
e flags adequadas, sem stubs falsos.

Nenhum arquivo com 94 nomes reais, código compilado do jogo ou objeto privado
é enviado ao GitHub. Os testes unitários usam exemplos sintéticos inspirados
na categoria dos seis símbolos originais, sem dados de jogo.

## Próximo bloqueio REAL

1. Rodar auditoria no `combined_aot_loader.o` privado da Etapa 89.
2. Relacionar serviços `nx` com fontes reais upstream e bibliotecas
   OpenOrbis (somente código público em workflows).
3. Executar link estrito do conjunto real + provedores, sem aceitar símbolos
   indefinidos; documentar erros, resolver ABI/stdlib/libm corretamente.
4. Completar `sdk` e `main`, integrar GPU/áudio/serviços para só então
   procurar primeira inicialização do jogo no console.

**Status:** nem eboot nem PKG de Castlevania. Nenhum resultado privado real foi
obtido com este instrumento até que `need.nm` seja inspecionado.
