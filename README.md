# Kazuma Traduções — Castlevania: Belmont's Curse | Pesquisa para PS4

> **Projeto independente da Kazuma Traduções.** Esta marca identifica as ferramentas, auditorias e adaptações originais deste laboratório, **não** a autoria ou a propriedade intelectual do jogo. Não somos afiliados nem endossados pelos titulares da obra. Todos os créditos originais e as licenças de componentes de terceiros devem ser preservados.
>
> **Identidade visual:** capas, ícone, banner, HUD e cenas originais não recebem marcas d'água. Uma assinatura discreta de contribuição técnica poderá entrar na seção de créditos/versão **somente depois de funcionamento real demonstrado**. Ferramentas e relatórios autorais já podem exibir a marca.

> **Estado atual: laboratório experimental; port do jogo ainda não demonstrado.** O repositório contém código e pipelines para compilar um homebrew independente de teste e produzir um PKG offline em CI. Isso **não** significa que o PKG tenha sido instalado/iniciado no PS4, nem que exista um port jogável de Castlevania. Não há binários comerciais do jogo ou `eboot.bin` do jogo neste repositório.

## O que existe neste repositório

- `src/input_adapter.*`: mapeamento C++ experimental entre botões DualShock 4 e botões Switch; **ainda não integrado ao driver ScePad do runtime do jogo**.
- `tools/audit_switch.py`: leitura superficial de cabeçalhos PFS0 dos arquivos NSP e do índice de um ZIP; não descriptografa nem valida dados inteiros.
- `tools/audit_apk.py`: auditoria estática das bibliotecas presentes num APK de Android.
- `tools/etapa12/` até `tools/etapa17/`: fontes, fixtures e scripts de testes independentes de homebrew; não incluem código comercial de Castlevania.
- `.github/workflows/kazuma-etapa17-paginas.yml`: pipeline de CI que tenta compilar, ligar, converter e empacotar o homebrew independente Test 06 em ambiente Linux. Se a execução passar, publica o PKG como artefato explicitamente **NÃO TESTADO** no console.
- `tools/etapa19/` e `.github/workflows/kazuma-etapa19-gates.yml`: testes e auditoria estática das interfaces de plataforma ainda ausentes; não geram PKG e não provam compatibilidade de runtime.
- `.github/workflows/testes.yml`: compila código auxiliar no Linux e roda testes por GitHub Actions; não é, isoladamente, uma compilação PS4.
- `docs/ETAPA_2_COMPARATIVO.md`: comparação das fontes C++ disponíveis e necessidades específicas do PS4.

## Como executar os testes auxiliares

```sh
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

Os pipelines das Etapas 17 e 19 têm instruções próprias nos arquivos `.github/workflows/`.

## Situação técnica e próximos marcos

O projeto [SwonDev/cstlvnia-blmont-to-macos](https://github.com/SwonDev/cstlvnia-blmont-to-macos) publica um recompilador AArch64 → C++, parâmetros específicos da versão Switch 1.1.0 e runtime que ainda tem dependências macOS/Android/Linux/Windows. Não publica código gerado do jogo nem implementação PS4 pronta. A documentação de [iHaiDeeZ/SMW](https://github.com/iHaiDeeZ/SMW) é referência para o uso de Clang, OpenOrbis e Mesa RADV em PS4 com *outro* jogo.

1. **Homebrew independente:** revisar logs e artefato da CI, confirmar integridade do PKG de teste e, somente com autorização do proprietário, testar instalação e inicialização no PS4 Slim.
2. **Runtime PS4:** completar e validar memória guest, carregamento de módulos, vídeo Vulkan/RADV/WSI, controles, áudio, filesystem e salvamentos.
3. **Recompilação do jogo:** validar a possibilidade de compilar os três módulos `main`, `sdk`, `subsdk0` para x86-64, somente a partir de materiais obtidos e utilizados de forma autorizada.
4. **Primeiro quadro:** integrar e executar o runtime com o jogo; medir estabilidade e desempenho antes de preparar arte e pacote final.

### Limites de evidência

- CI verde comprova apenas as etapas automatizadas executadas no runner Linux.
- Gerar ELF/OELF/`eboot.bin`/PKG offline não comprova instalação ou inicialização no PS4.
- Testes CPU 2D, símbolos Vulkan/RADV presentes ou auditorias estáticas não comprovam renderização do jogo.
- O homebrew de teste é independente e **não contém Castlevania**.

## Segurança e direitos

Não faça commit de ROMs, NSP/XCI/NCA, APK, arquivos `.keys`, `prod.keys`, `title.keys`, dumps de código do jogo ou dados proprietários. Nunca compartilhe chaves nem tokens de autenticação. Um projeto público deve conter apenas código próprio ou de terceiros reutilizado de acordo com sua licença. A arte do jogo foi preparada separadamente para uso privado, não incluída no repositório público.
