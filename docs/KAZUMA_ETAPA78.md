# Kazuma Etapa 78 — ligação dinâmica real do ExeFS e entradas AOT

## Objetivo

Depois da validação criptográfica da Etapa 77, examinar a estrutura `MOD0`, tabelas dinâmicas, símbolos importados/exportados e realocações de `main`, `sdk`, `subsdk0` locais, **sem publicar código ou dados comerciais**.

O verificador `tools/etapa78/exefs_linkage_probe.py` verifica a assinatura e SHA-256 originais do perfil da versão 1.1.0 antes de analisar os módulos.

## Resultado da inspeção privada de 5/11/2026

| Módulo | Símbolos dinâmicos | RELA | RELR |
|---|---:|---:|---:|
| main | 770 | 2.077 | 623.907 |
| sdk | 23.015 | 19.168 | 14.684 |
| subsdk0 | 10.395 | 15.924 | 3.355 |

Os únicos tipos normalizados encontrados foram `ABS64`, `GLOB_DAT`, `JUMP_SLOT` e `RELATIVE_RELR`. A agregação privada encontrou **1.213 nomes de importação únicos; 1.210 também aparecem definidos em algum dos três módulos; 3 não aparecem**. Isso **não** implica que restam apenas três funções para completar o port de PS4: a ligação ELF, o loader guest, a CPU, GPU, shaders e serviços do sistema ainda exigem integração.

Os três sem definição ExeFS são uma rotina de inicialização thread-local e duas referências de profiler. A inspeção privada dos campos ELF de `main` confirmou **bind=2 (weak) nas três**. O `runtime/src/loader.cpp` do upstream fixado resolve imports fracos ausentes colocando o addend no slot, sem acionar o erro `strict_imports`. Logo o inventário atual não encontrou import forte sem definição entre os três NSOs. Isso não prova que o restante do loader/serviços funciona no PS4.

## Como reproduzir localmente sem vazamento

Requer Python >=3.10 e `pip install lz4` para NSOs comprimidos (não inclua ROMs no repositório).

```sh
python3 tools/etapa78/exefs_linkage_probe.py \
  "/caminho/privado/ExeFS" \
  --report "/caminho/privado/etapa78.json"
```

O CLI busca o perfil público fixado em `tools/etapa77/upstream_build_1_1_0.json`; o relatório contém contagens sem nomes nem conteúdo binário do jogo. **Não** publique o relatório se contiver diretórios pessoais ou dados adicionais que tenha incluído manualmente.

## Testes sem jogo

```sh
python3 tests/test_exefs_linkage.py
ctest --test-dir build --output-on-failure
```

Fixtures com assinatura NSO0, MOD0, tabelas de símbolos e RELA artificiais. O CI não possui nem recebe os módulos reais.

## Bloqueios seguintes

1. Conferir no ambiente PS4 a semântica do loader guest para as três importações weak ausentes (upstream tem caminho explícito), sem silenciar falhas de símbolos obrigatórios.
2. Gerar AOT de `main`, `sdk`, `subsdk0` com recompilador AArch64→C++ fixado, mantendo fontes geradas privadas.
3. Compilar/linkar com runtime OpenOrbis/Mesa RADV e validar no console; sem substituir gameplay por demos.
4. Os relatórios 235–238 validam extração e inventário RomFS, mas a cobertura completa dos shaders exigidos pela build 1.1.0 e tradução NVN→SPIR-V **ainda não estão concluídas**.

**Status:** análise de entrada AOT avançada. Nenhum novo PKG, `eboot.bin` ou jogo jogável gerado.
