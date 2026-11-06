# Kazuma — Etapa 82: inspeção de `nx::unimpl` no AOT real

## O que foi descoberto (somente relatórios; C++ comercial permanece privado)

O relatório `unhandled 0` do recompilador **não significa ausência de chamadas `nx::unimpl` nos C++ emitidos**. `recomp/emit.py` do upstream fixado em `4043f21bb4f656d34cd17ba070238c7728d00631` emite, por exemplo, `udf`, palavras não decodificáveis e fallback de tratamento de exceções como `nx::unimpl`, sem necessariamente incrementar o contador `unhandled`.

Inspeção privada dos backups reais (somente contagem, arquivos comerciais não enviados ao GitHub):

| ExeFS | C++ inspecionados | unimpl encontrados | Interpretação |
|---|---:|---:|---|
| subsdk0 | 73 | 321 | 318 `udf`, 3 não decodificáveis |
| sdk | 136 | 879 | 575 **guardas padrão** de exceção; 301 `udf`; 2 não decodificáveis; 1 `stg` |
| main | 1.707 | **não inspecionado nesta etapa** | relatório AOT já indica duas `mov` sem handler |

**Importante sobre exceções:** os 575 `nx::unimpl(..., "destino de excepción sin generar")` são o ramo `default` do `switch(lp_)` gerado pelo upstream, **não 575 destinos de exceção necessariamente ausentes**. Os destinos listados pelo LSDA viram `case ...: goto ...`. A guarda é acionada apenas com destino inesperado.

`udf`/bytes não decodificáveis podem estar em padding, código inalcançável, ou serem armadilhas usadas intencionalmente pelo jogo. Não inferir *crash* de gameplay pelo número estático.

## Implementação

`tools/etapa82/aot_trap_audit.py` lê `code_*.cpp` **somente da pasta privada local**, uma unidade por vez, e produz JSON apenas de contagens, categorias e alguns offsets de amostra; não publica código ou strings do jogo. `tools/etapa79/aot_private.py` acrescenta campo separado `aot_static_trap_audit` após geração real, sem confundir `unhandled 0` com cobertura total.

Exemplo, dentro de ambiente privado após gerar AOT:

```sh
python3 tools/etapa82/aot_trap_audit.py "/caminho/privado/subsdk0-gerado" \
  --expected-units 73 --report "/caminho/privado/etapa82_subsdk0.json"
```

O relatório pode ser revisado localmente; não enviar arquivos `code_*.cpp`, `table.cpp`, módulos NSO ou chaves ao repositório público.

## Próxima etapa concreta

Compilar, isoladamente, uma unidade C++ **real** do `subsdk0` com OpenOrbis + os headers `nx` fixados. Essa ação somente verifica compilação e dependências; **não** gera o executável do jogo. Se compilar, expandir para mais unidades e medir custo/erros, antes de tentar link completo.

**Ainda não comprovado:** existência de `eboot.bin` jogável, link do AOT ao runtime PS4, correção semântica da `stg`, tratamento dinâmico de exceções, traduções NVN/SPIR-V.
