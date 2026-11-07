# Kazuma — Etapa 88-B: ABI real do carregador (07/11/2026)

O relatório `Kazuma_Etapa87_Link_Tabela_Resultado.json` fornecido pelo usuário confirma: 73 objetos e tabela de 14.173 funções compilados pelo OpenOrbis v0.5.4/Clang 18, link parcial aprovado, seis referências indefinidas: `nx::call`, `nx::unimpl`, `ceil`, `floor`, `fma`, `trunc`. Ainda **não** existe link final com runtime nem PKG.

## Novo teste real com fonte pública
No upstream fixado em `4043f21bb4f656d34cd17ba070238c7728d00631`, o `runtime/src/loader.cpp` implementa `nx::call(nx::CPU&, unsigned long)` e `nx::unimpl(nx::CPU&, unsigned long, char const*)`.

O workflow `.github/workflows/kazuma-etapa88-loader-abi.yml` compila o **loader verdadeiro**, diretamente com OpenOrbis e Clang 18, mais um probe sintético que apenas faz referência às duas assinaturas. Se o link relocável entre esses objetos eliminar as duas referências indefinidas, teremos evidência de compatibilidade ABI no alvo PS4. O teste não faz upload de nenhum objeto derivado de jogo.

O probe precisa incluir `<algorithm>` antes de `<nx/cpu.h>` para compatibilidade com o `<cmath>` da libc++ OpenOrbis; isso não altera o código original do upstream.

## Limites do resultado
Isso NÃO significa que `loader.cpp` + 74 objetos privados já foram ligados. O carregador real traz dependências adicionais em serviços `nx`, `plat`, HLE, memória, kernel e bibliotecas C++ que precisam ser resolvidas em um link estrito. As quatro funções `ceil`, `floor`, `fma`, `trunc` são esperadas da biblioteca matemática compatível no link final. Não se deve escrever stubs que apenas retornam sucesso para ocultar dependências.

O projeto possui uma Etapa 88 distinta de validação de limites TEXT em `src/port_core`; este teste independente é identificado como **88-B** para evitar confusão de numeração.

**Status:** aguardar CI antes de declarar aprovação; não houve eboot, PKG ou teste no PS4.
