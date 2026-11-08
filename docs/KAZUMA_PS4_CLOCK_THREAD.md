# Operação Castlevania — clock e identidade de threads reais no PS4

A auditoria de símbolos da PR #116 (`kazuma-posix-file-io-public-no-rom`)
identificou `nx::plat::monotonic_ns`, `sleep_ns`, `yield` e
`current_thread_id` ainda indefinidos no conjunto público.

O novo `src/ps4/platform_ps4_clock_thread.cpp` implementa:
- `CLOCK_MONOTONIC/clock_gettime`, sem usar hora civil para o relógio;
- `nanosleep` com repetição após `EINTR` e tratamento de valores negativos;
- `sched_yield`, não um retorno falso sem escalonamento;
- `scePthreadGetthreadid()` real do `libkernel` PS4 no alvo FreeBSD.
  Apenas o teste Linux usa `syscall(SYS_gettid)`, fora do PS4.

Workflow com OpenOrbis v0.5.4/Clang18 compila **24 fontes públicas**,
combina-as em um único link ELF relocável e exige os quatro providers
ausentes como símbolos definidos de verdade. O símbolo externo
`scePthreadGetthreadid` deve permanecer importado do SDK.
Teste host C++ verifica relógio monotônico, espera real e IDs distintos.

**Limites**: o CI não executa o código no PS4. Ainda faltam
`nx::plat::start_thread`, `exit_thread`, `data_root`, `setting`,
montagem real de SaveData e serviços restantes. Não confundir com
link executável concluído; NVN, STG/SVE e AOT privado também pendentes.
Não foi construído PKG nem `eboot.bin`.
