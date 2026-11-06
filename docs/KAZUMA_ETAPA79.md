# Operação Castlevania — Etapa 79 (AOT real, entradas privadas)

## O que esta etapa realmente entrega

O laboratório anterior usava um `nx::Module` artificial diretamente no emissor (Etapa 21). A Etapa 79 testa uma fronteira diferente: um **arquivo NSO0 sintético completo, com `MOD0`, tabelas `.dynamic` e símbolos**, fornecido ao comando real `python -m recomp` do upstream fixado. O CI exige `funcs.h`, `table.cpp`, `code_000.cpp`, `report.txt`, três instruções tratadas e zero instruções não suportadas no fixture.

O segundo componente é um orquestrador **local e privado** para o AOT real do jogo, começando por `subsdk0` (o menor módulo). Ele autentica o NSO por SHA-256 e Build ID da versão 1.1.0 (Etapa 77), confere o checkout do recompilador original e impede que o C++ gerado seja escrito dentro de qualquer diretório Git. **Este C++ é derivado de conteúdo comercial e deve permanecer exclusivamente privado.**

## Como usar em ambiente privado (Linux/Colab, NÃO GitHub Actions)

Requer Python >=3.10, `capstone==5.0.6`, `lz4==4.4.4`, memória e espaço. O notebook Megaware com Windows 7 32 bits não é um alvo apropriado para AOT de grandes módulos.

Em uma máquina privada, obtenha o projeto upstream público fixado:

```sh
git clone --filter=blob:none --sparse https://github.com/SwonDev/cstlvnia-blmont-to-macos.git upstream
git -C upstream checkout --detach 4043f21bb4f656d34cd17ba070238c7728d00631
git -C upstream sparse-checkout set recomp games/castlevania
python3 -m pip install capstone==5.0.6 lz4==4.4.4
```

Depois de ter a **cópia extraída do seu ExeFS privado** num diretório local, partindo da raiz deste workbench (`Castlevania-PS4-Port`):

```sh
python3 tools/etapa79/aot_private.py \
  --exefs "/caminho/privado/ExeFS" \
  --upstream "/caminho/privado/upstream" \
  --out "/caminho/temporario/fora-do-git/kazuma-aot-subSDK0" \
  --module subsdk0 \
  --timeout 3600
```

A saída deve estar fora de qualquer checkout Git e estar vazia. O comando não faz upload nem cria PKG. Ele registra `aot.stdout.txt`, `aot.stderr.txt`, `report.txt`, `code_*.cpp`, `table.cpp` e `etapa79_local.json`; nenhum arquivo do jogo ou AOT gerado deve ser colocado no GitHub. Se falhar, preserve o diagnóstico local; não infira sucesso do processo pela existência parcial dos arquivos. `--only-entry 0x...` é diagnóstico incompleto que **não** produz jogo linkável.

**Política:** não rodar AOT verdadeiro no CI público; CI recebe somente `synthetic.nso` fabricado de três instruções públicas. A árvore do jogo e os dados comerciais permanecem sob controle do usuário.

## Resultado anterior já estabelecido

- ExeFS `main`, `sdk`, `subsdk0` validados por hashes públicos da revisão 1.1.0.
- Metadados MOD0/relocações verificados na Etapa 78; imports fracos não resolvidos não precisam de implementações falsas.
- RomFS extraída (Etapa 235) e shaders NVN inventariados (Etapas 237-238), **ainda não traduzidos** integralmente para SPIR-V.

## Ainda falta para um port jogável

O AOT privado gera arquivos C++ correspondentes ao programa guest, não um `eboot.bin`. Depois ainda é preciso compilar/linkar com adaptadores reais do PS4, resolver semântica de CPU/loader e as integrações NVN→Vulkan/SPIR-V. Nem o teste sintético de CI nem o `etapa79_local.json` são prova de gameplay ou execução em hardware.
