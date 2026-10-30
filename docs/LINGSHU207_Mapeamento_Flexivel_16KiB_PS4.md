# Lingshu207 — mapeamento flexível de 16 KiB + permissões, diagnóstico independente

**Data do build:** 30/10/2026 UTC, ainda 29/10 no Brasil.

## Base real

No firmware PS4 Slim 13.52 do usuário, o diagnóstico Lingshu190 confirmou 18 reservas exatas e liberações individuais em seis bases (16KiB,1MiB,16MiB). O Lingshu206 confirmou cinco reservas simultâneas de 16MiB nas bases MODULES/HEAP/ALIAS/STACK/KERNEL e suas cinco liberações reversas. Nenhum desses testes fez um mapeamento gravável, `mprotect` ou leu/escreveu bytes.

## Novo experimento — NÃO integra na engine

O Lingshu207 é um homebrew de diagnóstico sem jogo, feito para observar:

1. `sceKernelMapFlexibleMemory(&address,0x4000,3,0)`, com `address=nullptr`: kernel escolhe novo endereço. **Não reaproveita nem altera** as cinco regiões já reservadas no Lingshu206.
2. Verifica retorno zero e ponteiro retornado não nulo, alinhado a 16KiB, sem wrap; recusa ponteiros anômalos.
3. Apenas após o mapeamento retornar sucesso, escreve e verifica dois bytes (primeiro e último) na página de 16KiB.
4. `sceKernelMprotect(addr,0x4000,1)`: muda para proteção somente leitura, lê novamente os dois bytes.
5. `sceKernelMprotect(addr,0x4000,3)`: restaura leitura/escrita.
6. `sceKernelMunmap(addr,0x4000)`: tenta liberar o intervalo retornado mesmo após falhas nas etapas de proteção. Se a limpeza falhar, registra estado inseguro; nunca relê após a liberação.

**Não** usa `MAP_FIXED`, reserva de guest VA, blocos gigantes, leitura do jogo, chaves, firmware comercial ou arquivos AOT. O mapeamento em si usa memória real do processo e, se houver uma anomalia não prevista pelo sistema, pode causar travamento: não afirmar segurança absoluta.

## Evidência reproduzível

GitHub Actions público: [run #40990915951](https://github.com/hansifelix/Castlevania-PS4-Port/actions/runs/40990915951), conclusão `success`, `runner_id=1000001496`, código na branch `lingshu207-flexible-mapping-16k-20261029`, SHA de commit `b4bfc91b98d9933a6bca007eedd96dfa14151151`.

Os oito testes Linux com mocks e ASan/UBSan passaram: sucesso RW→RO→RW, negação da API, erro que muda ponteiro, sucesso com ponteiro nulo, endereço desalinhado, falha na proteção RO, falha na restauração RW, falha de `munmap`. **São mocks e não evidência de hardware**.

Também compilou e linkou ELF PS4, produziu FSELF/EBOOT e gerou PKG genérico usando OpenOrbis fixado e empacotador público.

- Nome original do PKG: `IV0000-KAZM20700_00-LINGSHU207NATIVE.pkg`
- Tamanho conferido: `6619136` bytes
- SHA-256 conferido com `diagnostic-pkg.sha256` do artefato GitHub: `04893fc855b1c194bef79fe4a67204ffe1f90e60af91aa93f999e148e7404ca7`
- [Artefato PKG (ZIP com PKG e checksum)](https://github.com/hansifelix/Castlevania-PS4-Port/actions/runs/40990915951/artifacts/12948469738).
- Dois arquivos `.pkg` dentro do ZIP possuem SHA-256 idêntico; a cópia nomeada pelo content-ID foi extraída e oferecida ao usuário diretamente, sem modificação.

## Teste opcional no console

O programa não foi executado em PS4 ainda. Se decidir testá-lo em GoldHEN, é esperado exibir `MAPA 16K OK VERIFIQUE LOG` no caso de todas as operações terem sucesso, ou `MAPA PARCIAL VERIFIQUE LOG` caso contrário. Para confirmar, enviar o log (via FTP) de:

- `/data/lingshu207-flexible-16k.log`
- `/user/data/lingshu207-flexible-16k.log`
- `/mnt/usb0/lingshu207-flexible-16k.log`

Linha esperada no sucesso real: `LINGSHU207_FINAL=FLEXIBLE_16K_RW_RO_RW_AND_CLEANUP_OK_NOT_GAME`, com `LINGSHU207_SUMMARY mapped=1 io=1 readonly=1 rw_restored=1 cleanup=1 unsafe=0 complete=1`.

**Atenção**: mapeamento de 16KiB em endereço atribuído pelo kernel não prova que ele possa ser criado *dentro* de uma reserva guest de 4/6/64GiB. Tampouco prova boot `nx::boot()`, shaders, NVN→PS4 ou gameplay. Se a app travar ou o console se comportar anormalmente, interromper as tentativas.

**Estado:** `HOST_8_MOCKS=PASS` · `ELF=BUILT_CI` · `EBOOT=BUILT_CI` · `PKG=BUILT_CI` · `PS4_MAP_TEST=NOT_RUN` · `GAME_BOOT=NO`.
