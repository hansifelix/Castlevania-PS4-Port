# Kazuma Port Games BR — Etapa 49 — Integração REAL dos serviços básicos de host

**Objetivo:** após confirmar o resultado real da Etapa 48 (compilação de `nx::boot()` passou, link estrito falhou, 273 símbolos indefinidos no objeto), integrar funções básicas de `nx::plat` para um alvo PS4 sem fingir que o jogo está funcionando.

### Seis funções implementadas

| API | Contrato / implementação | Limitação explícita |
| --- | --- | --- |
| `headless()` | retorna false: a build não é headless | não testa GPU |
| `memguard_overlap_ns()` | retorna 0: não há memory guard ativo | proteção de memória do jogo NÃO implementada |
| `profile()` | retorna false: profiling amostral opcional indisponível | não substitui benchmark |
| `setting()` | lê variável `NX_*` se presente | sem painel de configurações |
| `data_root()` | diretório padrão `/app0`, com sobrescrita por `NX_DATA_ROOT` absoluta | **/app0 é somente leitura; NÃO implementar saves aí** |
| `exit_process()` | saída normal pela libc | sem alterações ao firmware |

A integração utiliza os 87 componentes públicos previamente compilados, o boot real e 8 APIs anteriores. Gera um novo objeto relocável, compara símbolos antes e depois (esperamos 6 APIs retiradas; o número total de pendências também pode mudar) e **tenta novamente a ligação executável estrita** com OpenOrbis. O linker não é instruído a ignorar símbolos ausentes.

### Conferir no GitHub Actions

A saída deve estar no artifact `kazuma-etapa49-delta-dependencias-boot-real-sem-pkg`, pasta `etapa49/`:

- `LEIA_PRIMEIRO.txt`: quantidade de APIs resolvidas e pendências reais restantes.
- `RELATORIO.json`: nomes e listas de pendências, introduzidas ou resolvidas.
- `COMPILACAO.log`, `LINK_PARCIAL.log`, `LINK_ESTRITO.log`: provas técnicas.
- `PLATAFORMA_PENDENTE.txt`: próximos trabalhos nativos prioritários.

**Checks verdes = auditoria e validação de 6 APIs feita corretamente**, não executável nem Castlevania no PS4. Não há PKG, ROM, NSP, APK, ExeFS, RomFS, AOT comercial ou assets. Os módulos AOT do jogo deverão ser produzidos LOCALMENTE a partir de cópia legitimamente obtida, sem upload ao GitHub público.

### Próximo trabalho importante

1. Integração **real** de `reserve/commit/decommit` com gestão de memória do PS4, testada em isolamento.
2. Threads, entrada e áudio reais do PS4.
3. Backend gráfico NVN/Vulkan compatível com a GPU do PS4.
4. Pipeline privado de módulos AOT da versão do jogo correta; então tentar executar `nx::boot()` com módulos, recursos e shaders reais.

Não afirmar compatibilidade ou jogabilidade até os testes no hardware comprovarem.
