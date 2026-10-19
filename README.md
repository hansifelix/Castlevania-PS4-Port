# Castlevania: Belmont's Curse — pesquisa de portabilidade para PS4

> **Estado atual: laboratório experimental, não port jogável.** Este repositório **não** contém jogo, binários recompilados, `eboot.bin`, PKG instalável nem ferramentas para converter um NSP automaticamente.

## O que existe neste repositório

- `src/input_adapter.*`: mapeamento C++ experimental entre botões DualShock 4 e botões Switch; **ainda não integrado ao driver ScePad**.
- `tools/audit_switch.py`: leitura superficial de cabeçalhos PFS0 dos arquivos NSP e do índice de um ZIP; não descriptografa nem valida dados inteiros.
- `tools/audit_apk.py`: auditoria estática das bibliotecas presentes num APK de Android.
- `tests/`: testes sem dados de jogos, com arquivos sintéticos.
- `.github/workflows/testes.yml`: compila código auxiliar no Linux e roda testes por GitHub Actions. **Isso não é a compilação de um aplicativo PS4.**
- `docs/ETAPA_2_COMPARATIVO.md`: comparação de fontes C++ disponíveis e necessidades específicas do PS4.

## Execução dos testes

```sh
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

## Situação da pesquisa

O projeto [SwonDev/cstlvnia-blmont-to-macos](https://github.com/SwonDev/cstlvnia-blmont-to-macos) publica um recompilador AArch64 → C++, parâmetros específicos da versão Switch 1.1.0 e runtime que ainda tem dependências macOS/Android/Linux/Windows. Não publica código gerado do jogo nem implementação PS4 pronta. A documentação de [iHaiDeeZ/SMW](https://github.com/iHaiDeeZ/SMW) é referência para o uso de Clang, OpenOrbis e Mesa RADV em PS4 com *outro* jogo.

### Próximos marcos reais

1. Compilar e iniciar um **homebrew simples e independente** no PS4 Slim (SDK/eboot/PKG e teste no console).
2. Portar e testar funções de plataforma (memória, vídeo Vulkan/RADV, controles e áudio).
3. Validar a possibilidade de compilar os três módulos `main`, `sdk`, `subsdk0` para x86-64, somente a partir de materiais obtidos e utilizados de forma autorizada.
4. Integrar, executar e medir desempenho; somente depois preparar arte e PKG do jogo.

## Segurança e direitos

Não faça commit de ROMs, NSP/XCI/NCA, APK, arquivos `.keys`, `prod.keys`, `title.keys`, dumps de código do jogo ou dados proprietários. Nunca compartilhe chaves nem tokens de autenticação. Um projeto público deve conter apenas código próprio ou de terceiros reutilizado de acordo com sua licença. A arte do jogo foi preparada separadamente para uso privado, não incluída no repositório público.
