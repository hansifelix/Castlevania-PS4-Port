# Etapa 66: testar sinalizacao GNM exigida ao suspender PS4

## Evidencia da etapa65 (Klog real)
- 16 quadros apresentados e GPU ociosa: `vkDeviceWaitIdle` retornou sucesso.
- Ao fechar, falhou `sceApplicationSuspend` com:
  `Can't suspend pid:162. submitDone() is not called.`
  `CPU_FAULT_SUBMITDONE_TIMEOUT_IN_SUSPEND_ASYNC`.

## Hipotese
O Mesa/RADV empacotado contem `sceGnmSubmitDone`, mas seu codigo WSI
so chama quando `ORBIS_SUBMIT_DONE` esta definido. O loop da etapa65
nunca chamou essa funcao explicitamente. Esta ausencia pode explicar
por que o PS4 recusa a suspensao mesmo com a GPU ociosa.

## Teste controlado
Uma renderizacao, `vkDeviceWaitIdle`, `sceGnmAreSubmitsAllowed`
e, se permitido, `sceGnmSubmitDone` (resultado registrado no Klog).
Depois o aplicativo permanece inativo. Feche somente via menu PS4.

Busque no Klog:
`KAZUMA66: GNM_ARE_SUBMITS_ALLOWED`
`KAZUMA66: RESULTADO_sceGnmSubmitDone`
E verifique se o erro de `sceApplicationSuspend` reaparece.

Verde no GitHub Actions NAO prova o fechamento no PS4 real.
Nao e um port do Castlevania; sem arquivos comerciais.
