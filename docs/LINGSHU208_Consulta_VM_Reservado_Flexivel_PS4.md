# Lingshu208 — consultar reserva virtual vs. mapa flexível, sem alterar páginas

Data: 30/10/2026. **Diagnóstico homebrew INDEPENDENTE, sem dados de jogo.** Não é port jogável do Castlevania.

## Por que este teste existe

Três testes anteriores executaram **no PS4 real**:
- Lingshu190: 18/18 reservas e liberações pequenas **individuais** com `sceKernelReserveVirtualRange`.
- Lingshu206: cinco regiões de 16 MiB **simultâneas**, nos endereços exatos da engine, e cinco liberações reversas.
- Lingshu207: uma página flexível **separada**, de 16 KiB, escrita/leitura, proteção RO/RW e liberação.

Ainda **não sabemos** como o kernel descreve uma reserva sem páginas mapeadas em contraste com uma página flexível realmente mapeada; tampouco sabemos se `sceKernelMapFlexibleMemory` pode aproveitar uma região guest já reservada **sem sobrescrever mappings**. O Lingshu208 foi desenhado para observar, não forçar essa combinação.

## Operação segura e limitada

1. `sceKernelReserveVirtualRange` de **16 KiB** na base guest de MODULES (`0x4000000000`) sem `MAP_FIXED`.
2. Se reserva exata, `sceKernelVirtualQuery(addr, 0, &info, sizeof(info))` observa a **reserva guest**, sem tocar seus bytes.
3. `sceKernelMapFlexibleMemory(&ptr, 16 KiB, 3, 0)` pede **endereço escolhido pelo kernel**, totalmente independente da reserva; exige ponteiro válido, alinhado e sem sobreposição.
4. `sceKernelVirtualQuery(ptr, 0, &info, sizeof(info))` observa **a região flexível mapeada**, sem escrever ou ler seus bytes.
5. Libera o mapeamento flexível e depois a reserva guest; em falha, registra estado inseguro no log. Nenhuma região grande ou recurso proprietário é acessado.

**Metadados de `OrbisKernelVirtualQueryInfo`:** descobrimos erro real de compilação: o cabeçalho do SDK OpenOrbis v0.5.4 obtido como tarball não fornece o membro `start_addr` que aparece em outra versão do cabeçalho publicada no repositório. Para **não adivinhar o layout binário** e não interpretar falsamente `isCommitted` ou `prot`, o diagnóstico registra apenas o código de retorno, o tamanho da estrutura e um **prefixo de até 48 bytes brutos** devolvidos pela consulta no buffer tipado zero-inicializado. Isso não lê dados da página; revela somente os metadados fornecidos pela API. Decodificação por campos fica pendente de ABI comprovada.

## Evidência de build/host (NÃO console)

- PR draft: [#70](https://github.com/hansifelix/Castlevania-PS4-Port/pull/70), branch `lingshu208-virtual-query-20261030`.
- CI: [GitHub Actions #41003747815](https://github.com/hansifelix/Castlevania-PS4-Port/actions/runs/41003747815), `conclusion=success`, runner alocado.
- Cenários host mocks com ASan/UBSan: sucesso com dois tipos de query e limpeza em ordem reversa; reserva negada; reserva deslocada; query indisponível; mapa negado; mapa com endereço nulo; falha de liberação. Todos aprovados.
- Compilou/linkou ELF PS4, gerou EBOOT e empacotou PKG genérico.
- PKG original: `IV0000-KAZM20800_00-LINGSHU208NATIVE.pkg`.
- Tamanho: **6.619.136 bytes**.
- SHA-256: `c0e1b87b877fac802c0634e113848a1ffece48f95ea9cabe8641698002e49df3`, **conferido localmente** com o arquivo `diagnostic-pkg.sha256` produzido no CI.
- [Artefato ZIP do GitHub](https://github.com/hansifelix/Castlevania-PS4-Port/actions/runs/41003747815/artifacts/12954158929) contém duas cópias PKG com hash idêntico, mais checksum; o PKG foi extraído sem modificações para entrega direta.

## Teste opcional no PS4

**Não houve execução do Lingshu208 no console.** A consulta `sceKernelVirtualQuery` usa estrutura tipada conforme SDK e flags 0, mas não há prova de comportamento no firmware do usuário. Se decidir testar em PS4 com GoldHEN, o app pode falhar, não mostrar a tela ou travar, apesar de não fazer escrita de dados no mapeamento.

Log esperado (FTP):
- `/data/lingshu208-virtual-query.log`
- `/user/data/lingshu208-virtual-query.log`
- `/mnt/usb0/lingshu208-virtual-query.log`

`LINGSHU208_QUERY name=GUEST_RESERVED status=OK` e `...FLEXIBLE_MAPPED status=OK` indicariam duas consultas com retorno 0; `LINGSHU208_FINAL=TWO_VM_TYPES_QUERIED_AND_RELEASED_NOT_ENGINE` requer as duas consultas e duas liberações bem-sucedidas. Se a consulta não for suportada, o programa ainda deve tentar liberar a memória e registrar `PARTIAL_CLEAN_NOT_ENGINE`.

**NÃO PROVA:** mapeamento dentro de guest VA existente, coexistência de regiões 4/6/64 GiB, commit/decommit da engine, boot de `nx::boot()`, shaders, renderer NVN→PS4 ou gameplay.

**Status atual:** `HOST_QUERY=PASS` · `NATIVE_PKG=BUILT_CI` · `PS4_HARDWARE_208=UNTESTED` · `CASTLEVANIA_PLAYABLE=NO`.
