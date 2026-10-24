# Kazuma — Etapa 68: integração da ponte nx::plat (Vulkan/PS4)

## Progresso real da Etapa 67
O teste fornecido pelo usuário mostrou triângulo renderizado no console real, GPU Liverpool via RADV, 512 quadros relatados, e suspensão via menu PS com `SCE_OK` em 58 ms. A gravação é menor que 20 s, então esse critério de estabilidade contínua ainda não está demonstrado. O Klog aponta avisos secundários durante limpeza e ícone; não alterar o renderer validado.

## O que a Etapa 68 faz
Esta etapa conecta três funções do contrato do runtime público (Etapa 62) ao aplicativo que já apresentou Vulkan na TV:
- `nx::plat::vulkan_get_instance_proc_addr()`
- `nx::plat::vulkan_surface_extension()`
- `nx::plat::vulkan_create_surface()`

A ponte invoca o loader Mesa/RADV **real** usando o mesmo SDK verificado da Etapa 67. A API `nx::plat` é exercitada **na mesma execução que renderiza e apresenta quadros**. O código-base da Etapa 67 é copiado e transformado com verificações estritas; não se altera o baseline.

**Importante**: esta integração gráfica representa um avanço do lado das interfaces de plataforma. Não compila nem executa o próprio `nx::boot()` ou módulos de jogo. É um teste de interface, não uma fase jogável.

## Logs para verificar no console

- `KAZUMA68: BRIDGE_RUNTIME_VULKAN_PS4_REAL; SEM_JOGO`
- `KAZUMA68: NX_PLAT_GIPA=OK`
- `KAZUMA68: ok   nx::plat::gipa->vkCreateInstance`
- `KAZUMA68: ok   nx::plat::vulkan_create_surface`
- `KAZUMA68: NX_PLAT_SURFACE=OK`
- `KAZUMA68: PRESENTACAO_CONTINUA_INICIADA`
- `KAZUMA68: frame N apresentado ...`
- Encerramento pelo menu PS: `SCE_OK`, sem timeout de SubmitDone.

## Bloqueios para ver a primeira fase *real* de Castlevania
O repositório não contém nem executa os módulos recompilados (`main`, `sdk`, `subsdk0`) do jogo ARM64; a Etapa 48 contou 273 dependências ainda indefinidas (antes das APIs da Etapa 49). Também faltam adaptação de memória, áudio, controles, shaders e empacotamento privado dos dados do usuário. Renderizar um triângulo via API `nx::plat` não elimina essas lacunas.

## Segurança, direitos e limites
- Sem assets, código e executáveis comerciais no GitHub público.
- Não gerar pacote com o jogo ou simulacro de gameplay em nome dele.
- Não promete fase jogável amanhã: a execução da fase depende de um pipeline AOT e runtime cuja compatibilidade ainda não foi demonstrada.
- CI verde atesta apenas compilação; cada teste precisa ser executado no console.
