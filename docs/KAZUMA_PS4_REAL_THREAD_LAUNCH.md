# Operação Castlevania — execução real de threads no PS4

Após a PR #117, relógio monotônico, sleep, yield e identificação da thread
estavam presentes, mas faltavam três primitivas exigidas pelo runtime:
`nx::plat::start_thread`, `exit_thread` e `exit_process`.

Este patch implementa **criação real de threads destacadas**, respeitando
o tamanho da pilha solicitado pelo chamador, com uso de APIs **libkernel
scePthread*** na compilação OpenOrbis v0.5.4 e POSIX pthread apenas no
teste host Linux. O contexto `ThreadFn/arg` é alocado antes de iniciar
a thread e liberado dentro dela. Falhas de atributos/criação abortam o
processo explicitamente: nunca fingimos ter lançado uma thread.
`exit_thread` usa `scePthreadExit`; `exit_process` usa `_exit` para
evitar destrutores do processo enquanto threads guest operam.

O workflow compila as **25 fontes públicas reais** em um link parcial
`ld.lld -r`, exige as três assinaturas `nx::plat` definidas e as
importações `scePthreadCreate`, `scePthreadExit` e atributos
`scePthreadAttrSetstacksize/Setdetachstate`. Executa teste POSIX host
de duas threads, ID real, tamanho de pilha observado e término
explícito da terceira thread sem acionar `exit_process`.

**Ainda faltam** serviços de ambiente PS4, montagem de dados/savedata,
renderização NVN, SVE/STG e os 1.916 objetos privados AOT no
link estrito. Compilar/linkar não é prova de boot PS4 ou PKG jogável.
