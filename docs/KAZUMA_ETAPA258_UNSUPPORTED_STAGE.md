# Etapa 258 — rejeição fail-closed de shader stages não suportados

## Achado no runtime upstream pinado

- O `ShaderStage` reconhece Vertex, Fragment e Compute; Geometry e outros execution models ficam `Unknown`.
- `reflect_spirv` aceitava `Unknown` e continuava refletindo descriptors.
- `stage_bit` tratava qualquer valor diferente de Vertex/Fragment como Compute.
- O draw gráfico percorre apenas VS/FS, mas o `program_layout` recebia o conjunto inteiro de shaders. Um Geometry/Unknown podia portanto ter seus descriptors marcados como Compute e ser ignorado pelo pipeline gráfico de dois estágios.

## Correção experimental

O script `tools/link/patch_unsupported_shader_stage_failclosed.py` modifica somente um checkout temporário do upstream pinado:

1. `reflect_spirv` rejeita execution models não reconhecidos antes de retornar reflexão.
2. `stage_bit` mapeia explicitamente Vertex/Fragment/Compute; Unknown retorna zero.
3. O draw aborta se qualquer shader do programa tiver stage Unknown, antes de `program_layout` e antes de criar pipeline.

O patch não adiciona Geometry support. Se o Geometry shader do índice RomFS 238 for obrigatório, continuará bloqueado até implementação NVN→Vulkan completa, incluindo descriptor slot, interface GS→FS, topology e capability `geometryShader`.

## Validação nesta PR

- Fixture host do patch: drift, symlinks e idempotência.
- SPIR-V synthetic host: Vertex/Fragment/Compute aceitos; Tessellation, Geometry, Kernel, Task/Mesh NV e Ray execution models rejeitados.
- Fixture multi-entrypoint: a primeira entrypoint suportada é a selecionada pelo runtime; primeira entrypoint unsupported é rejeitada.
- Teste compilado do `stage_bit` do patch de produção: flags Vertex/Fragment/Compute exatas, Unknown e enum inválido retornam zero.
- Cross-compile OpenOrbis dos 88 objetos runtime/metadata e 14 adapters PS4 via Etapa 98, sem AOT ou assets comerciais.

## Limites

Não traduz shaders, não compila o bundle GPU, não cria EBOOT/PKG e não executa GPU, PS4 ou gameplay. O patch é uma barreira de segurança de estágio, não solução para Geometry.


## Etapa 265 — fail-closed para stages NVN ligados fora de VS/FS (26/11/2026)

**Achado adicional:** o helper upstream `graphics_program_shaders()` só recolhe os slots NVN 0 (Vertex) e 1 (Fragment). Geometry (slot 2) e Tessellation (slots 3/4) podiam estar ligados em `StagePrograms`, mas ser silenciosamente descartados antes do guard Etapa 264; por isso, o guard de draw não os via.

**Correção experimental no patch pinado:**
- Se qualquer slot 2–4 estiver ligado, o helper acrescenta um sentinela nulo à lista graphics.
- O guard Etapa 264 rejeita esse sentinela antes de `program_layout`, evitando continuar com pipeline VS/FS incompleto.
- Compute (slot 5) permanece fora do draw gráfico e não é rejeitado por esta regra.

**Regressão host:** compila a função helper extraída do patch de produção; verifica Vertex+Fragment, cada slot Geometry/Tessellation bloqueado, Compute separado e limpeza de estado entre chamadas. Workflow host Etapas 264–265, sem SDK/AOT/ROM/assets.

**Limites:** não implementa Geometry/Tessellation. Nenhum shader comercial, bundle real, GPU, EBOOT/PKG, boot PS4 ou gameplay foi testado.
