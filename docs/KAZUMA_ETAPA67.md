# Kazuma Etapa 67: triangulo continuo + SubmitDone na WSI

A Etapa 66 comprovou que uma chamada GNM SubmitDone retornou 0x00000000
apos um unico frame e permitiu suspender o aplicativo no PS4. A imagem,
entretanto, nao permaneceu na televisao.

Esta etapa retoma a apresentacao continua da Etapa 64 e habilita
ORBIS_SUBMIT_DONE=1 antes de criar a instancia Vulkan. Assim, o Mesa WSI
pode sinalizar GNM SubmitDone no limite de cada frame, sem duplicar a
chamada no codigo do aplicativo.

Titulo: Kazuma Triangulo Vulkan 67. Title ID: BREW91267.

Criterios do teste real:
1. Triangulo visivel continuamente por pelo menos 20 segundos.
2. Klog mostra KAZUMA67: ORBIS_SUBMIT_DONE=1 e frame ... apresentado.
3. Procurar wsi/orbis: sceGnmSubmitDone at the frame boundary.
4. Fechar pelo menu PS e verificar se a suspensao termina sem
   submitDone() is not called / CPU_FAULT_SUBMITDONE_TIMEOUT.

O build verde significa apenas compilacao e pacote gerado, nao
funcionamento comprovado no console. Nao contem o jogo Castlevania.
