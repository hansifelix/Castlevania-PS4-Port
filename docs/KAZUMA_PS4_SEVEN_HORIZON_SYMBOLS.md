# Castlevania PS4 — sete dependências internas Horizon localizadas por artefato real

Origem: resultado público de GitHub Actions na PR #114, execução
`42450386961`, artefato de auditoria `kazuma-kernel-boot-public-no-rom`.
O link parcial com **19 fontes** passou, porém expôs **133 símbolos
distintos não resolvidos, fora dos providers já validados**. Entre eles,
sete funções internas concretas do runtime upstream:

- `nx::init_tls_block` e `nx::set_tls_template`: **svc_process.cpp**;
- `nx::map_transfer_memory`, `nx::unmap_transfer_memory` e
  `nx::set_thread_core_mask`: **svc_process.cpp**;
- `nx::get_info`: **svc_info.cpp**;
- `nx::log_recent_files`: **hle_fs.cpp**.

Novo workflow soma essas **três fontes verdadeiras** do runtime MIT fixado
`4043f21bb4f656d34cd17ba070238c7728d00631` ao conjunto anterior,
totalizando **22 fontes C++ reais** com OpenOrbis v0.5.4 e Clang 18.
Um único `ld.lld -r` e o gate `--require-horizon-services` exigem
definição única das sete assinaturas, sem símbolos internos indefinidos.
A versão de 19 arquivos mantém seu gate independente; nenhum corpo vazio
ou objeto AOT falso foi criado para passar os testes.

**O que esta etapa NÃO faz:** chamar a compatibilidade de TLS/transfer
semântica pronta no console, resolver por completo libc++, `nx::plat::`
(restam serviços de arquivos, threads, relógios), os bindings gráficos
NVN, instruções STG/SVE ou o link executável PS4. Três tabelas AOT
proprietárias permanecem deliberadamente indefinidas no CI público,
sem ROM, EBOOT nem PKG.
