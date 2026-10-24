# Kazuma Port Games BR — Etapa 74 (Display PS4)

## Contexto verificável

Na Etapa 73, o objeto relocável do `nx::boot()` tinha **9 funções `nx::plat` ainda pendentes**:

- Três de áudio: `audio_open`, `audio_submit`, `audio_queued`.
- Seis de display: `create_window`, `release_window`, `screen_size`, `window_size`, `window_generation`, `window_minimized`.

Essas contagens decorrem dos relatórios oficiais da PR #61, não de execução do jogo.

## Objetivo desta etapa

Integrar **seis contratos de display** a partir de chamadas reais do OpenOrbis:
`sceVideoOutOpen` → `sceVideoOutGetResolutionStatus` → `sceVideoOutClose`.

O PS4 não oferece uma janela de desktop equivalente a HWND. Por isso, `create_window`
retorna um descritor opaco com dimensões obtidas do VideoOut do console, que
é usado pelo código de plataforma. A ponte Vulkan implementada anteriormente
trabalha com superfície **headless** e ignora explicitamente o ponteiro
`native_window`. Nada aqui simula a criação de janelas clássicas de desktop.

**Cautela:** consultas são feitas por um *handle temporário* VideoOut que é
fechado antes de qualquer apresentação. A compatibilidade simultânea com o
Mesa/WSI do PS4 não foi testada; caso existam disputas de handle, devemos
alterar a implementação e validar no hardware antes de prosseguir.

**Cautela:** `window_minimized()` assume display disponível quando a consulta
VideoOut funciona, mas ainda **não implementa os estados de suspensão/resume**
do PS4. `window_generation()` incrementa ao criar ou liberar o descritor, não
monitora automaticamente mudanças físicas do monitor.

O código **não desenha triângulos, não inicia o jogo e não gera PKG**.

## Testes e medidas

1. Testes Python verificam que as seis assinaturas que estavam pendentes foram
   removidas de `llvm-nm` **após** integrar o objeto real de display e que o
   linker as considera definidas.
2. Teste C++ no host usa um mock **identificado como mock** para avaliar os
   contratos, dimensões, erros de consulta, cache e fechamento do VideoOut.
3. GitHub Actions recompila o arquivo C++ **com os cabeçalhos reais OpenOrbis**,
   conecta-o aos objetos da Etapa 73 e tenta um link estrito.
4. Mesmo com check verde, `FALHOU_LINK_ESTRITO` significa que **não existe ELF
   executável**, nem jogo. Audio, ABI, Vulkan/Mesa e AOT seguem pendentes.

## Próximo bloqueio decisivo

A Etapa 70 mostrou NSP base e update contendo NCAs **ainda não extraídos e
descriptografados**. Para compilar o Castlevania verdadeiro, o upstream usa
módulos `main`, `sdk` e `subsdk0`, mais RomFS, que devem corresponder à revisão
1.1.0. Os arquivos comerciais e qualquer chave ficam **apenas localmente**.
Sem essas entradas, nenhuma quantidade de APIs do host gera o jogo.

**NÃO** enviar NSP, NCA, NSO, ROM, chave ou assets ao GitHub. Também não
presumir que uma atualização `[v65536]` corresponda à revisão 1.1.0 apenas
pelo nome do arquivo; conferir IDs/versões de conteúdo é obrigatório.

## Status esperado (não garantido)

Se as assinaturas conferirem e o OpenOrbis compilar, esperamos reduzir as
pendências `nx::plat` de 9 para 3 (áudio), **não** o total de símbolos indefinidos,
que pode subir com os imports verdadeiros `sceVideoOut*`.

**Critério de sucesso:** relatório auditável de símbolos do `nx::boot()`;
execução real e desempenho no PS4 continuam explicitamente não verificados.
