# Kazuma Traduções — Castlevania: Belmont's Curse | Pesquisa para PS4

> **Projeto independente da Kazuma Traduções.** Esta marca identifica as ferramentas, auditorias e adaptações originais deste laboratório, **não** a autoria ou a propriedade intelectual do jogo. Não somos afiliados nem endossados pelos titulares da obra. Todos os créditos originais e as licenças de componentes de terceiros devem ser preservados.

> **Estado em 15/11/2026: laboratório experimental; o port do jogo ainda não foi demonstrado.** Há uma pilha pública de runtime PS4 compilada parcialmente, integração relocável NVN/Vulkan/Mesa-RADV, auditorias privadas de integridade dos objetos AOT e uma ferramenta para procurar provedores do SDK. Isso ainda **não** equivale a um link executável completo, EBOOT/PKG do jogo, instalação, boot ou gameplay no PS4. Não há binários comerciais de Castlevania nem `eboot.bin` do jogo neste repositório.

## Estado técnico confirmado

### Runtime público PS4 e vídeo

- A Etapa 76 compilou 87 fontes C++ únicas do runtime upstream fixado e metadados do jogo, totalizando **88 objetos ELF relocáveis PS4**.
- Foram compilados **14 objetos de provedores PS4** para serviços de plataforma, memória, controle, display, áudio, IO, configuração, relógio/threads e entrada do runtime.
- O ELF relocável combinado inclui NVN, o vkloader oficial e o archive Mesa/RADV real com zlib pareado. Os três entrypoints ICD reais estão definidos nesse conjunto.
- O gate público exige 39 provedores e não encontrou provedores públicos obrigatórios ausentes ou duplicados. A auditoria das bibliotecas OpenOrbis encontrou provedores para **455 de 458 imports fortes**; os três restantes correspondem aos módulos AOT privados esperados.
- O resultado do link estrito público foi classificado como **`PUBLIC_LINK_CLOSED_AOT_PENDING`**: as referências restantes são `nx_module_main`, `nx_module_sdk` e `nx_module_subsdk0`. Portanto, o link executável completo ainda não passou.
- NVN/RADV está em integração parcial. A presença do loader e do ICD no ELF relocável não comprova inicialização Vulkan, criação de dispositivo, apresentação de frame ou renderização no PS4.

Detalhes: [Etapa 76 — fechamento da pilha pública PS4/NVN-RADV](docs/KAZUMA_ETAPA76.md).

### Integridade e símbolos AOT privados

- A Etapa 90-C confirmou **1.916/1.916 objetos** MAIN, SDK e subsdk0 como ELF64 little-endian ET_REL x86-64, com hashes correspondentes aos manifests analisados e zero objetos inválidos. A auditoria foi somente-leitura; os backups permanecem privados.
- As Etapas 91–95 acrescentaram inventário de símbolos, candidatos internos, metadados ELF das definições duplicadas e proteção contra sobrescrita de relatórios.
- O relatório privado v2 validado para a Etapa 96 contém **39 nomes indefinidos únicos** sem provedor AOT interno, distribuídos por **14.174 referências consumidor-objeto-símbolo**. Também registra 101 nomes duplicados em 16.602 localizações; todas as localizações duplicadas desse relatório estão classificadas como WEAK/COMDAT.
- Nomes mangled, caminhos locais, objetos e relatórios completos são dados privados e não devem ser publicados no GitHub, no chat ou em artefatos públicos.

Detalhes: [Etapa 90](docs/KAZUMA_ETAPA90.md), [Etapa 91](docs/KAZUMA_ETAPA91.md) e [triagem Etapa 92](docs/KAZUMA_ETAPA92_TRIAGEM_AOT.md).

### Etapa 96 — candidatos de provedores SDK/runtime

A ferramenta `tools/etapa90/private_aot_sdk_provider_audit.py` compara nomes exatos de símbolos indefinidos com definições presentes em bibliotecas e objetos indicados pelo operador. Ela preserva a identidade do membro de archives, distingue definições ambíguas, evita duplicação por raízes sobrepostas, não segue symlinks e falha fechada diante de leitura parcial.

A suíte pública usa apenas inventários e bibliotecas sintéticas. A CI mais recente registrada, [#43711590791](https://github.com/hansifelix/Castlevania-PS4-Port/actions/runs/43711590791), terminou com sucesso em 15/11/2026: **33/33 CTest**, 9 testes do auditor estrutural, 12 do inventário de símbolos e 13 do scanner de provedores.

**Pendente:** a varredura privada com as bibliotecas binárias reais do OpenOrbis 0.5.4 e os objetos compilados do runtime PS4 correspondentes ainda precisa ser executada no ambiente que contém esses arquivos. Os testes sintéticos não substituem essa execução e não provam compatibilidade ABI.

Detalhes e comando privado: [Etapa 96 — auditoria de provedores](docs/KAZUMA_ETAPA96_PROVIDER_AUDIT.md).

### Etapa 97 — barreira de evidências ABI

A ferramenta `tools/etapa90/private_aot_abi_evidence_gate.py` vincula a revisão ao SHA-256 exato do relatório da Etapa 96, confere hashes de headers/declarações e exige revisão individual de cada definição candidata. Um resultado completo continua **não sendo prova de ABI nem autorização de link**. CI usa somente fixtures sintéticas.

Detalhes: [Etapa 97 — revisão ABI](docs/KAZUMA_ETAPA97_ABI_REVIEW.md).

## Próximos marcos

1. Reunir, no ambiente privado, a cópia exata do OpenOrbis 0.5.4 e os objetos do runtime PS4 compilados com a mesma toolchain.
2. Executar a Etapa 96 sem extrair ou publicar arquivos comerciais; manter o JSON completo privado e compartilhar somente contagens agregadas.
3. Executar a Etapa 97 e revisar individualmente cada definição candidata, mantendo hashes e evidências no ambiente privado. A barreira não prova ABI nem autoriza link.
4. Só depois preparar um link privado controlado sem stubs falsos. Se o link executável fechar, avançar para a geração controlada de EBOOT/PKG e teste de instalação/boot no PS4 autorizado.
5. Integrar e validar vídeo/WSI, controles, áudio, filesystem, SaveData e primeiro frame antes de declarar qualquer estado jogável.

## Componentes e ferramentas existentes

- `src/input_adapter.*`: mapeamento experimental entre botões DualShock 4 e botões Switch; ainda não integrado ao driver ScePad do runtime do jogo.
- `src/ps4/`: provedores e contratos de plataforma PS4 desenvolvidos para o laboratório.
- `tools/etapa90/`: auditoria estrutural privada, inventário de símbolos e busca privada de candidatos a provedores.
- `tools/link/`: gates de compilação, classificação de link e diagnósticos da pilha PS4.
- `.github/workflows/testes.yml`: compila código auxiliar no Linux e executa testes com dados fictícios; não é, isoladamente, um build final de Castlevania para PS4.
- As pipelines de NVN/RADV e do homebrew independente são diagnósticos separados e devem ser interpretadas conforme a documentação de cada etapa.

## Como executar os testes auxiliares

```sh
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
python3 tests/test_private_aot_object_audit.py
python3 tests/test_private_aot_symbol_inventory.py
python3 tests/test_private_aot_sdk_provider_audit.py
python3 tests/test_private_aot_abi_evidence_gate.py
```

A CI pública usa fixtures sintéticas para os auditores privados. Um resultado verde valida os testes executados no runner Linux, não a resolução dos símbolos comerciais nem a execução no console.

## Referências externas e escopo

O projeto [SwonDev/cstlvnia-blmont-to-macos](https://github.com/SwonDev/cstlvnia-blmont-to-macos) publica um recompilador AArch64 → C++, parâmetros específicos da versão Switch 1.1.0 e um runtime com dependências de outras plataformas. Ele não publica código gerado do jogo nem uma implementação PS4 pronta. A documentação de [iHaiDeeZ/SMW](https://github.com/iHaiDeeZ/SMW) é uma referência para uso de Clang, OpenOrbis e Mesa RADV em PS4 com outro jogo.

## Segurança e direitos

Não faça commit de ROMs, NSP/XCI/NCA, APK, arquivos `.keys`, `prod.keys`, `title.keys`, dumps de código do jogo, objetos AOT comerciais, shaders privados ou relatórios integrais com símbolos/caminhos. Nunca compartilhe chaves nem tokens de autenticação. O repositório deve conter somente código próprio ou de terceiros reutilizado de acordo com sua licença. Arte e dados comerciais do jogo permanecem fora do repositório público.
