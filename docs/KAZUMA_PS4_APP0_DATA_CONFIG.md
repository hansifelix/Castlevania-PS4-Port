# Operação Castlevania — raiz real /app0 e configuração somente leitura

Depois da PR #118, `nx::plat::data_root`, `setting` e `log_line`
continuavam sem implementações públicas no PS4.

A implementação `src/ps4/platform_ps4_app0_config.cpp` agora:

- Usa `/app0`, ponto de montagem do pacote PS4, **somente** na
  compilação `-DKAZUMA_PS4=1`.
- Antes de devolver a raiz, verifica via `stat()` que as pastas reais
  `/app0/analysis/` e `/app0/extract/romfs/` existem. Se não
  estiverem lá, registra diagnóstico e **aborta explicitamente**:
  não inventa arquivos comerciais nem retorna uma raiz vazia.
- Implementa `setting(key)` opcional por `/app0/kazuma-settings.cfg`
  com formato `key = value` (comentários `#` ou `;`).
  A leitura não escreve no pacote. Ausência do config retorna string
  vazia como no runtime PC; chaves inválidas são recusadas.
- Usa `sceKernelDebugOutText(0, "%s\\n", line)` para logs do PS4,
  com formato constante (linha de jogo não é interpretada como format).
- Para testes **somente Linux**, a variável `KAZUMA_TEST_APP0_ROOT`
  substitui `/app0` por diretório temporário; isso não entra no
  objeto PS4.

O CI OpenOrbis v0.5.4/Clang18 compila **26 fontes C++ públicas**,
liga-as com `ld.lld -r` e exige definições únicas desses três
provedores, além dos anteriores. Testes host exercitam as pastas reais,
configuração, chaves inválidas e **falha abortando** quando faltam dados.

**Limites importantes:**
- Ainda não há jogo empacotado. As pastas exigidas são uma verificação
  de estrutura, **não** prova de que análise/ROMFS ou objetos AOT
  estejam completos ou corretos.
- `/app0` é somente leitura. O upstream atual também usa
  `writable_root() == data_root()` no PS4, portanto
  **montagem segura de dados salvos permanece pendente**.
- Nenhum dado proprietário é versionado. Não há `eboot.bin`, PKG,
  link executável, renderer NVN nem verificação em hardware.
- Próximo passo: separar dados empacotados de salvamentos graváveis,
  em vez de tentar escrever no pacote read-only.
