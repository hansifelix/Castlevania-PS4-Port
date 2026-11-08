# Operação Castlevania — fechamento conjunto dos 13 callbacks de vídeo

Esta etapa verifica **em conjunto**, com o `OpenOrbis v0.5.4`,
`Clang 18`, `ld.lld -r` e headers `nx/runtime.h` originais do MIT upstream,
as implementações públicas `src/ps4/castlevania_*.cpp` responsáveis
pelos **13 callbacks nx_castlevania_*** que apareciam indefinidos no relatório
privado de 1.916 objetos AOT.

O workflow **não** usa os objetos AOT proprietários: combina 8 objetos
produzidos de 8 arquivos C++ públicos sob o alvo PS4 em um único arquivo
ELF **REL relocável**. Em seguida o gate `video_callback_closure.py`
exige as 13 assinaturas exatas como definições de símbolos globais
e a resolução interna de `configure_native`, `select_render`,
`ready`, `native_size`, `render_size` e `refresh_video_choices`.

O gate não confunde referências ao runtime `nx::call`, `nx::log`,
`nx::fatal`, libc++ e bibliotecas de plataforma com callbacks faltantes.
Essas referências externas ainda podem existir e **não** são resolvidas
pelo link parcial. Usa apenas texto de `llvm-nm -C` para auditoria;
testes unitários com símbolos sintéticos simulam definição ausente,
duplicada, extra e provider não resolvido.

**Interpretação correta de um PASS**: todos os callbacks públicos estão
compilados juntos com as assinaturas e provedores testados; não significa
que todos os símbolos do ELF comercial gigante estejam resolvidos,
não verifica semântica CPU/GPU e não afirma boot no console.

Próximos bloqueios: ligação final com o código AOT privado em ambiente
do usuário, implementação real dos serviços de runtime do sistema,
semântica STG/MOV SVE e conversão do pipeline NVN/Vulkan/PS4.
Nenhum objeto proprietário/ROM/PKG/eboot é enviado para o GitHub.
