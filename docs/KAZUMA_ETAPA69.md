# 🐘 KAZUMA 69 — ELEFANTE RUNNER (PS4)

Prototipo interativo solicitado como substituto dos testes repetidos de triangulos.

## Controles e cenario

- Elefante cinza corre automaticamente em um mato verde com arvores ao fundo.
- Cercas de madeira aproximam-se da direita.
- **DualShock 4: X (CROSS) faz o elefante pular** (apenas quando esta no chao).
- Ao superar uma cerca, aumenta o contador interno; se atingir, o jogo registra colisao e continua.
- Encerrar com o menu PS4, como na Etapa 68.1.

Graficos **2D procedurais**: elipses e retangulos Vulkan, sem imagens/arquivos comerciais. Isto e um pequeno minijogo tecnico original, nao uma fase do Castlevania.

## Aprendizado aproveitado

O Klog da Etapa 68.1 confirmou:
- `VKLOADER_INSTANCE_REGISTRADA=OK`;
- GPU Liverpool RADV detectada;
- 512 frames registrados;
- suspensao SCE_OK em 67ms.

Preservamos a criacao de VkInstance via `ps4-vkloader`, ORBIS_SUBMIT_DONE=1 e o WSI, e trocamos o triangulo por cenas procedurais atualizadas a cada frame. A API real ScePad foi incorporada, mas ainda nao testada com o hardware do usuario.

## Marcadores essenciais no Klog

- `KAZUMA69: PAD_INIT=... PAD_HANDLE=...` — se handle negativo, falta corrigir o controle.
- `KAZUMA69: ELEFANTE_NA_SELVA; APERTE_X_PARA_PULAR`
- `KAZUMA69: CONTROLE_X_DETECTADO buttons=...`
- `KAZUMA69: PULO_X`
- `KAZUMA69: CERCA_SUPERADA total=N` ou `KAZUMA69: COLIDIU_CERCA total=N`
- `KAZUMA69: frame N apresentado`
- `Suspend App ... => SCE_OK`

Se houver somente tela preta, **nao insistir em varias tentativas**; coletar Klog e video. Teste no hardware so apos CI verde. Os testes CI nao comprovam que o renderizador ou a leitura do pad funcionarao no console.

## Limitacoes

Nao existe ainda `nx::boot()` em execucao, nem modulos AOT `main/sdk/subsdk0`, nem recursos ou fases do jogo comercial. Este teste exercita parte independente da plataforma (Vulkan + controle), nao resolve os bloqueios restantes do port.
