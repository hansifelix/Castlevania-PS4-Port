# Operação Castlevania — integração do kernel Horizon real (PS4)

Esta etapa amplia o link parcial da PR #113: compila agora **19 fontes C++ públicas**
para `x86_64-pc-freebsd12-elf` com OpenOrbis v0.5.4 e Clang 18.

Além do loader, `nx::boot`, memória PS4, registro dos três módulos, 13 callbacks
do Castlevania e o provedor real `sceVideoOut*`, inclui quatro fontes
originais do runtime MIT em revisão imutável
`4043f21bb4f656d34cd17ba070238c7728d00631`:

- `runtime/src/kernel.cpp`: handles, estado de threads e escalonamento básico;
- `runtime/src/kernel_thread_control.cpp`: `thread_checkpoint`/suspensão cooperativa;
- `runtime/src/kernel_watch.cpp`: `kernel_init`, relatório de hang e backtrace guest;
- `runtime/src/ipc.cpp`: dispatcher HIPC e registro de serviços.

O teste exige definições conjuntas de `nx::kernel_init`, `nx::create_main_thread`,
`nx::current_cpu`, `nx::thread_checkpoint`, `nx::backtrace` e
`nx::handle_get`, além dos 13 providers originais e da interface VideoOut.
Um único `ld.lld -r` faz o diagnóstico do conjunto, sem inventar
corpos vazios para satisfazer o linker. Objetos internos do jogo
`nx_module_main`, `nx_module_sdk` e `nx_module_subsdk0`
DEVEM permanecer indefinidos no CI público: as tabelas AOT pertencem
ao ambiente privado do projeto.

**ATENÇÃO:** IPC contém serviços genéricos do upstream, alguns dos quais
ainda não implementam semântica real. Link parcial e presença de definições
não provam que esses serviços funcionam no PS4. Esta etapa NÃO é link final,
não prova inicialização de `nnMain`, não implementa NVN/SVE/STG
e não gera `eboot.bin` ou PKG. O inventário de símbolos não publica
objetos ou dados privados do jogo.
