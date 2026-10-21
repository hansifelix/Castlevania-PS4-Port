# Kazuma Port Games BR — Etapa 7: onde estão os provedores dos símbolos?

## Evidência anterior (artefato da Etapa 6)

O arquivo `resumo.json` do artifact da Etapa 6 confirmou quatro objetos ELF relocáveis e 34 símbolos indefinidos **distintos** na ligação parcial. Isso é normal e **não é prova de execução**. As dependências se dividem em:

- **7 símbolos concretos do próprio runtime `nx`**: `handle_get`, `kernel_alloc`, `free_thread_count`, `log`, `kstate::g_k`, `kstate::t_self`, `heap_size`;
- **1 inicializador fraco de TLS** associado a `nx::kstate::t_self`;
- **7 funções da libc**: `bcmp`, `memchr`, `memcpy`, `memset`, `strlen`, `strtoul`, `tolower`;
- **19 referências relacionadas a libc++, C++ ABI/RTTI/TLS, mutexes e memória**.

### Fontes públicas candidatas

| Símbolo(s) | Arquivo provável do upstream | Situação |
|---|---|---|
| `nx::handle_get`, `nx::free_thread_count`, `nx::heap_size`, `nx::kstate::g_k`, `nx::kstate::t_self` | `runtime/src/kernel.cpp` | Código-fonte identificado; compilação cruzada a comprovar |
| `nx::kernel_alloc` | `runtime/src/memory.cpp` | Código-fonte identificado; compilação cruzada a comprovar |
| `nx::log` | `runtime/src/loader.cpp` | Código-fonte identificado; compilação cruzada a comprovar |

O presente workflow recompila **somente fontes originais e públicas** dessas três unidades e confronta os símbolos definidos com as 34 referências do objeto combinado da Etapa 6. Também tenta uma **ligação adicional relocável (`ld.lld -r`)** usando as unidades novas que compilarem.

## Regras de conclusão

- Compilar novos objetos com alvo `x86_64-pc-freebsd12-elf` **não** demonstra que funcionam no PS4.
- A ligação parcial pode manter símbolos indefinidos. A presença de bibliotecas da libc, libc++, C++ ABI e TLS ainda precisa ser verificada especificamente contra o SDK.
- `PASS` só significa que os **três fontes candidatos compilaram** e a ligação **parcial** ocorreu. O `resumo.json` mostra quantas dependências originais os candidatos cobrem.
- `FAIL` significa que algum código-fonte candidato não compilou ou a ligação parcial falhou; o artefato guarda os motivos.
- **Nenhum** NSP, NCA, APK, jogo, eboot, PKG ou executável é utilizado/gerado. Não instalar nada no PS4 nesta etapa.
- Este experimento não testa código ARM64 recompilado do jogo, carregamento de módulos, Vulkan, áudio, saves nem jogabilidade.

**PR só deve receber merge após revisão dos logs e do resumo.**
