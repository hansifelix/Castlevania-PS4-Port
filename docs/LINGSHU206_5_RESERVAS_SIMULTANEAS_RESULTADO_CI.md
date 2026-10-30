# Lingshu 206 — cinco reservas simultâneas de 16 MiB, sem jogo

**Data do build:** 30/10/2026 UTC (29/10 no Brasil). **Status:** compilação PS4 e PKG produzidos pelo GitHub CI; **nenhuma execução no PS4 neste novo teste**.

## Motivação e evidência anterior
No PS4 Slim FW 13.52 do usuário, o Lingshu190 executou de verdade: 18 de 18 reservas exatas e liberações nativas bem-sucedidas, em seis endereços distintos e tamanhos de 16 KiB/1 MiB/16 MiB. Entretanto, eram reservas **sequenciais**, liberadas antes da seguinte. O teste Lingshu206 é novo: mantém até **cinco reservas de 16 MiB simultâneas** para MODULES/HEAP/ALIAS/STACK/KERNEL, sem commit, sem acessos à memória, sem `MAP_FIXED`, sem dados comerciais.

## Código fonte
- `tools/lingshu-concurrent-ps4/concurrent_policy.h`: reserva com validação de endereço, leitura de retorno, interrupção diante de negação, deslocamento e anomalias, com liberação de todas as reservas conhecidas em **ordem inversa**. Em erro de limpeza registra estado incerto.
- `native_concurrent_bridge.cpp`: conexão isolada com `sceKernelReserveVirtualRange` e `sceKernelMunmap`.
- `native_concurrent_console.cpp`: apresentação na tela, status honesto e log via FTP.
- `test_concurrent_policy.cpp` e `run_host_tests.sh`: cenários de mocks Linux para cinco reservas, negação na terceira, deslocamento, falha de limpeza, alteração inesperada de ponteiro e ponteiro nulo com sucesso da API.
- Workflow `.github/workflows/lingshu206-five-concurrent-pkg.yml`: usa OpenOrbis público, compila/linka ELF, converte EBOOT e empacota PKG genérico com script público fixado por commit.

## Evidência verificável de compilação

**GitHub Actions:** [run #40979029191](https://github.com/hansifelix/Castlevania-PS4-Port/actions/runs/40979029191) — `conclusion: success`, `runner_id=1000001478`, head commit `8be70d59fab9912776433d627617d2b55738f71d`. A suíte host testou e aprovou seis cenários:

```text
LINGSHU206_FIVE_HELD_REVERSE_RELEASE=PASS_MOCK
LINGSHU206_DENIAL_ROLLBACK=PASS_MOCK
LINGSHU206_RELOCATION_RELEASES_ACTUAL_AND_ROLLBACK=PASS_MOCK
LINGSHU206_CLEANUP_FAILURE_UNSAFE=PASS_MOCK
LINGSHU206_ERROR_CHANGED_POINTER_STOP=PASS_MOCK
LINGSHU206_NULL_SUCCESS_STOP=PASS_MOCK
LINGSHU206_HOST_SUITE=PASS_LINUX_MOCK_NOT_PS4
```

**PKG real gerado e exportado**, não testado em firmware:
- Nome original: `IV0000-KAZM20600_00-LINGSHU206NATIVE.pkg`.
- Tamanho: **6.619.136 bytes**.
- SHA-256 extraído e verificado contra `diagnostic-pkg.sha256`: `60ea53b3b3992b06b668c7ebceffddb724a43df3ae7eb479169fd42825204a76`.
- [Artefato da compilação (ZIP contendo o PKG e checksum)](https://github.com/hansifelix/Castlevania-PS4-Port/actions/runs/40979029191/artifacts/12944086855) com retenção limitada.
- O arquivo `.pkg` foi extraído desse artefato, sem modificações, e oferecido diretamente ao usuário no chat.

## Teste em console — voluntário e não executado nesta etapa

Este diagnóstico manipula apenas **reservas de endereços virtuais**, sem tocar dados ou mapear RAM física. Apesar das precauções, chamadas nativas experimentais podem travar o aplicativo ou o console; não há garantia de comportamento em todo firmware. Usar somente GoldHEN/homebrew no próprio console já configurado, sem alterar sistema. Se ocorrer travamento, não repetir continuamente.

**Log esperado**, se acessível:
- `/data/lingshu206-five-simultaneous-16m.log`
- `/user/data/lingshu206-five-simultaneous-16m.log`
- `/mnt/usb0/lingshu206-five-simultaneous-16m.log`

**Linha que indicaria cinco reservas simultâneas exatas e depois liberadas:**
`LINGSHU206_FINAL=FIVE_16M_SIMULTANEOUS_EXACT_AND_RELEASED_NOT_GAME`, juntamente a um `SUMMARY` com `attempts=5 exact=5 released=5 release_failed=0 unsafe=0 coexisted=1 safe=1`.

Mesmo esse resultado **não** comprovaria reservas de 4/6/64 GiB, `commit/decommit`, simultaneidade de regiões com tamanhos completos, boot de `nx::boot`, renderer ou gameplay do Castlevania.

**Status:** `FIVE_WAY_HOST_MOCKS=PASS` · `PS4_EBOOT_LINK=PASS_CI` · `PS4_PKG=BUILT_CI` · `PS4_5_WAY_HARDWARE=NOT_TESTED` · `GAME=NOT_BOOTED`.
