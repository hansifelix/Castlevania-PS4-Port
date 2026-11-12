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


---

# Etapa 90-B — auditoria somente-leitura da integridade dos backups AOT (12/11/2026)

A auditoria de inventário de 11/11 encontrou 381 arquivos relevantes, 4.437 membros compactados e 339 arquivos em `Kazuma_Traducoes_AOT_Privado`. A cobertura nominal reportada foi de 1.707 objetos MAIN (0000–1706), 136 SDK (000–135) e 73 subsdk0 (000–072), totalizando 1.916. O inventário não tinha lacunas nem índices duplicados; ainda faltava verificar cada cabeçalho ELF e confrontar os manifests.

## Ferramenta nova

`tools/etapa90/audit_private_aot_objects.py` faz leitura somente-leitura de arquivos soltos e membros ZIP e TAR.GZ, sem escrever arquivos extraídos no Drive. Para cada `code_NNN.o`:

- Calcula SHA-256;
- Valida ELF64 little-endian, ET_REL e x86-64;
- Reconhece os intervalos de índices de MAIN, SDK e subsdk0;
- Conta réplicas idênticas de backup separadamente de conflitos de hash;
- Confronta manifests JSON e SHA256SUMS legíveis por módulo/índice;
- Detecta nomes de membros ZIP/TAR duplicados e arquivos compactados ilegíveis.
- Reconhece TAR.GZ/TGZ e lê cada membro por stream somente-leitura para validar objetos e hashes, sem materializar arquivos no Drive.
- Inventa um inventário de extensões, assinaturas binárias e nomes de membros para investigar lotes históricos.

Não compila, não liga, não move, não apaga, não renomeia e não publica conteúdo comercial. O relatório contém somente metadados, hashes e caminhos relativos.

## Execução privada

```sh
python3 tools/etapa90/audit_private_aot_objects.py \
  --root "/caminho/privado/Kazuma_Traducoes_AOT_Privado" \
  --report "/caminho/privado/fora-da-pasta-auditada/RELATORIO_ETAPA90B.json"
```

O relatório deve ficar fora da pasta de entrada. A ferramenta não grava arquivos extraídos: ZIP e TAR.GZ são lidos por streams somente-leitura. Arquivos 7Z/RAR ainda aparecem no inventário como formatos detectados, mas seus membros não são inspecionados. Se os manifests estiverem em formato não reconhecido ou não cobrirem os 1.916 índices únicos, o resultado será `PASS_STRUCTURE_ELF_MANIFESTS_INCOMPLETE`, nunca integridade completa.

## Estados

- `PASS_STRUCTURE_ELF_AND_MANIFESTS`: todos os índices presentes, todas as cópias ELF64 ET_REL x86-64 e hashes dos 1.916 índices únicos confirmados em manifests legíveis.
- `PASS_STRUCTURE_ELF_MANIFESTS_INCOMPLETE`: cobertura e cabeçalhos ELF aprovados, mas manifests incompletos/não reconhecidos.
- `FAIL_OR_INCOMPLETE`: lacunas, índices fora da faixa, conflitos de hash, ELF/arquitetura incorretos ou arquivos compactados ilegíveis.

O workflow público executa testes apenas com ELF sintético. Isso valida o auditor, não a integridade dos arquivos privados. O resultado real depende de rodar a ferramenta sobre a pasta privada.

## Próxima ação

Executar a auditoria privada antes de qualquer compilação ou link. Preservar todos os backups originais. Só depois de resolver eventuais conflitos e obter um relatório completo planejar a integração dos objetos já existentes com a toolchain OpenOrbis.


Notebook Colab pronto para executar esta etapa na mesma conta Google do projeto: `notebooks/Auditoria_Leitura_AOT_Etapa90B_Colab.ipynb`. Ele monta o Drive, procura `Kazuma_Traducoes_AOT_Privado`, executa o auditor e cria um JSON novo sem sobrescrever relatórios anteriores. Compartilhar somente esse JSON de metadados; não enviar objetos nem fontes AOT.
