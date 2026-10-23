# KAZUMA ETAPA 65 — Testar o fechamento apos 16 frames Vulkan

## Evidencia da Etapa 64 no PS4 Slim
Houve renderizacao real na TV, com apresentacao de mais de 1.024 quadros.
Ao fechar pelo menu PS, o Klog mostrou:
`CPU_FAULT_SUBMITDONE_TIMEOUT_IN_SUSPEND_ASYNC` e `submitDone() is not called`.
O bug apareceu durante renderizacao continua; isso NAO prova que o loop seja a unica causa.

## Experimento
Novo PKG com Title ID `BREW91265` (nao sobrescreve o 64).
Apresenta 16 frames, chama `vkDeviceWaitIdle`, para de enviar comandos GPU
e permanece em `sleep(1)`, sem sair de `main`.
Mantem os mesmos shaders Vulkan, SDK e Mesa/RADV usados no teste anterior.

## Resultado que procuramos no Klog
- `KAZUMA65: setup complete - presenting`
- `KAZUMA65: frame 0 presented`
- `KAZUMA65: ok   vkDeviceWaitIdle(after last present)`
- `KAZUMA65: IDLE_APOS_16_FRAMES`
- Ao fechar o aplicativo, verificar se o erro de suspensao reaparece.

## Teste
1. Instale o PKG novo sem apagar o antigo.
2. Inicie captura de Klog, execute o novo app e aguarde o triangulo.
3. Deixe a tela aberta por 5 a 10 segundos.
4. Pressione PS, escolha **Fechar aplicativo** (sem desligamento forcado).
5. Envie o Klog para analisar sucesso ou nova falha.

## Limites
Este e um experimento diagnostico, nao a correcao definitiva de todas as falhas.
Checks verdes validam build/empacotamento, NAO fechamento no PS4 real.
Nao inclui arquivos comerciais nem o codigo do Castlevania.
