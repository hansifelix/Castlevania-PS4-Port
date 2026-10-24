# Kazuma Port Games BR — Etapa 72: scePthread nativo

## Contexto medido (relatório da Etapa 71, run 40070140123)

- Testes da Etapa 71 passaram, PR #59 integrada.
- As 3 APIs `start_thread`, `exit_thread`, `yield` foram definidas por um objeto C++.
- O link parcial mostrou **268 símbolos antes e 272 depois**, incluindo sete novas dependências, como `pthread_create` e `sched_yield`.
- O link estrito do runtime continua **FALHOU_LINK_ESTRITO**; seis símbolos relacionados a módulos do jogo faltam.
- Isto indica que o avanço de APIs `nx::plat` não significa executável funcional.

## Objetivo da Etapa 72

Substituir o backend `pthread_*` do protótipo da Etapa 71 por `scePthread*` do `libkernel` no alvo FreeBSD/PS4 (OpenOrbis), sem duplicar implementações no link:

1. `nx::plat::start_thread` → `scePthreadCreate`, `scePthreadAttr*`, `scePthreadDetach`;
2. `nx::plat::exit_thread` → `scePthreadExit`;
3. `nx::plat::yield` → `scePthreadYield`;
4. `nx::plat::current_thread_id` → `scePthreadGetthreadid`;
5. `nx::plat::set_thread_name` → `scePthreadRename(scePthreadSelf(), nome)`.

### Como o build é feito

O workflow da Etapa 72 reproduz a compilação pública já validada até o objeto parcial da **Etapa 50**, então liga o **novo objeto nativo** (em vez de juntar `etapa71_threads.o`, o que produziria símbolos duplicados). Em seguida tenta o *link estrito* e publica o relatório real de símbolos, sem esconder os erros.

No CI o código é exercitado com um **mock Linux** de `scePthread` que prova o fluxo de API e o contrato básico; **não é execução PS4**. O compilador OpenOrbis compila o ramo real para x86-64 FreeBSD, e um analisador exige que o objeto importe as funções `scePthread*` ao invés de `pthread_create` e correlatas.

### Limitações reais

- As APIs nativas podem exigir ajustes após o teste da toolchain ou testes no PS4.
- Nem `link -r` nem `clang++ -c` equivalem a inicialização do jogo.
- Um check verde neste workflow significa compilação, mock testado e auditoria, **não** um EBOOT/PKG nem Castlevania funcionando.
- O exeFS/RomFS da cópia do jogo e a recompilação dos módulos ainda serão necessários em momento posterior.
- Arquivos comerciais não entram no repositório.

## Resultado esperado

`relatorios/etapa72/LEIA_PRIMEIRO.txt` mostra contagem real, status do link, bibliotecas importadas e símbolos pendentes. Se houver erro, abra `COMPILACAO.log`, `LINK_PARCIAL.log` ou `LINK_ESTRITO.log`.
