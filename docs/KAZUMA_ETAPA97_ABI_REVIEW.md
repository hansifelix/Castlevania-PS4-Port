# Kazuma Etapa 97 — barreira de evidências ABI para AOT

**Status:** ferramenta pública de validação de pacote de evidências; entradas e relatórios reais permanecem privados.

## Objetivo

A Etapa 96 encontra candidatos por nome exato em bibliotecas/objetos do SDK e runtime. Isso não demonstra que um símbolo possui assinatura, convenção de chamada, versão, relocations, layout de tipos ou dependências compatíveis com o consumidor AOT.

A Etapa 97 acrescenta uma barreira antes de qualquer link privado. Ela vincula a revisão ao SHA-256 exato do relatório da Etapa 96 e exige uma decisão individual para **cada definição candidata**, inclusive cada membro de archive ambíguo.

## Evidência exigida por candidato

Cada registro privado em `candidate_reviews` identifica exatamente `root`, `path`, `member` e `nm_type` do relatório de provedores, informa um veredito (`compatible`, `incompatible` ou `insufficient_evidence`) e contém:

- Caminho absoluto de um header real, SHA-256 do arquivo e linhas da declaração com SHA-256 do trecho exato.
- Identidade do SDK, compilador, target triple e revisão do runtime no nível do pacote.
- Revisão explícita de versão do símbolo, relocations, convenção de chamada, layout de tipos, dependências transitivas e resolução esperada pelo linker.
- Revisor identificado e horário ISO-8601 com fuso.

Os booleanos de revisão precisam ser explícitos. Para `compatible`, todos devem ser `true`. Para `incompatible`, é obrigatório declarar um motivo e pelo menos uma verificação não pode estar aprovada. Evidência insuficiente permanece bloqueante.

## Execução privada

Execute primeiro a Etapa 96 com os binários correspondentes ao SDK e runtime que realmente serão usados. Depois prepare um JSON privado seguindo o esquema `kazuma-private-aot-abi-review-v1`, com `provider_scan_sha256`, `target` (`sdk_release`, `compiler`, `target_triple`, `runtime_revision`) e `candidate_reviews`.

Calcule o vínculo com o relatório exato:

```bash
sha256sum RELATORIO_ETAPA96_PROVEDORES_PRIVADO.json
```

Cada definição candidata deve aparecer uma única vez. Para um símbolo com múltiplos candidatos, todas as definições precisam ser revisadas e exatamente uma pode receber `compatible`.

Execute a barreira:

```bash
python3 tools/etapa90/private_aot_abi_evidence_gate.py \
  --provider-scan "/caminho/privado/RELATORIO_ETAPA96_PROVEDORES_PRIVADO.json" \
  --reviews "/caminho/privado/REVISOES_ABI_PRIVADAS.json" \
  --report "/caminho/privado/RELATORIO_ETAPA97_ABI_PRIVADO.json"
```

Relatórios existentes não são sobrescritos: a ferramenta cria sufixos `_v2`, `_v3` etc. A sobrescrita exige `--overwrite-report`. O relatório não pode ficar na pasta dos arquivos de entrada nem substituir o header analisado.

## Critério de conclusão

O status `ABI_EVIDENCE_REVIEW_COMPLETE_NOT_LINK_PROOF` exige:

- Relatório da Etapa 96 completo, sem erros de leitura ou symlinks ignorados, com contagens coerentes.
- Uma revisão para cada definição candidata, sem candidato omitido ou duplicado.
- Header e trecho da declaração com hashes correspondentes aos bytes locais.
- Exatamente um candidato compatível por símbolo e nenhuma lacuna sem provedor.

Esse status **não** significa ABI provada, não autoriza o linker e não gera ELF executável, EBOOT, PKG ou instalação. A ferramenta registra explicitamente `abi_compatibility_proven=false` e `link_authorized=false`; o conteúdo dos campos ainda depende da veracidade da análise humana. Mesmo um pacote completo deve ser seguido por revisão independente do contrato e por um link controlado, sem stubs falsos.

## Evidência privada suplementar — SDK (16/11/2026)

Foi recuperado um pacote privado complementar com os três objetos SDK que faltavam no relatório anterior. A auditoria local confirmou integridade do TAR.GZ, correspondência dos três SHA-256 do manifesto e cabeçalhos ELF64 little-endian ET_REL para x86-64. O manifesto identifica OpenOrbis v0.5.4 / Clang 18 e a mesma origem AOT previamente registrada.

Somado aos 133 objetos SDK já verificados nos lotes privados anteriores, o conjunto estrutural do SDK fica em **136/136**. Isso fecha somente a presença/integridade estrutural dos objetos; não demonstra ABI, não substitui a varredura Etapa 96 dos provedores SDK/runtime e não autoriza link.

## Etapa 91 — inventário privado recomposto (16/11/2026)

Uma auditoria local somente-leitura dos pacotes privados do Dropbox reconstruiu o inventário dos três módulos:

- 319 pacotes: 285 MAIN, 24 SDK e 10 subsdk0.
- **1.916/1.916 objetos** ELF64 little-endian ET_REL x86-64; zero índices ausentes, duplicados ou objetos inválidos.
- Todos os hashes de objetos conferem com seus manifests; zero falhas de leitura ou divergências.
- 101 nomes de símbolos têm definições duplicadas, cobrindo 16.602 localizações; os metadados de binding/tipo/visibilidade estão completos.
- No inventário AOT, 39 nomes indefinidos não têm definição interna, cobrindo 14.174 referências consumidor-objeto-símbolo: 8 da categoria nx_runtime, 23 C++ ABI, 6 libm e 2 compiler runtime. Outros 99.972 nomes indefinidos têm pelo menos um candidato AOT por nome exato.

O relatório completo contém nomes mangled e permanece apenas no ambiente privado; nada disso foi publicado. Este resultado reconstitui a Etapa 91, mas **não substitui a varredura Etapa 96**: ainda falta comparar esses 39 nomes com as bibliotecas OpenOrbis v0.5.4 e os objetos reais do runtime PS4. Correspondência de nome não prova ABI.

## Privacidade e testes

Nomes mangled, caminhos privados, hashes de headers e relatórios completos devem permanecer fora do repositório, chat e artefatos públicos. A CI usa apenas fixtures sintéticas e headers temporários; não valida os binários privados do projeto.

A bateria cobre integridade do relatório de provedores, símbolos em categorias conflitantes, hashes do header e da declaração, membros ambíguos, ausência de candidato, revisões faltantes, timestamps com fuso e a regra de nunca autorizar link.
