# Kazuma — Etapa 77: identificar módulos reais da revisão 1.1.0

## Avanço técnico

A Etapa 76 verifica formato NSO0 e limites de segmentos. A 77 compara os três módulos `main`, `sdk`, `subsdk0` **com SHA-256 e Build ID exatos** do arquivo público `games/castlevania/build.json` em [SwonDev/cstlvnia-blmont-to-macos](https://github.com/SwonDev/cstlvnia-blmont-to-macos/blob/4043f21bb4f656d34cd17ba070238c7728d00631/games/castlevania/build.json), revisão fixa `4043f21bb4f656d34cd17ba070238c7728d00631`.

Esse é um **gate de identidade dos arquivos de entrada** para recompilação AOT. Não é um jogo, não executa código ARM64, não configura Vulkan e não compila um PKG.

## Uso totalmente local (após extração privada/legítima)

Na raiz do checkout, em computador com Python 3.8+:

```sh
python3 tools/etapa77/verify_revision.py "/caminho/para/ExeFS" --report "/caminho/privado/etapa77.json"
```

O diretório deve conter exatamente estes nomes de arquivos: `main`, `sdk`, `subsdk0`. Se o status for `EXEFS_PERFIL_1_1_0=CONFERE`, cada arquivo corresponde ao NSO de referência por SHA-256 e Build ID. Caso contrário, `NÃO CONFIRMADO` — pode haver revisão diferente, extração incompleta ou reempacotamento NSO. **Um resultado negativo não comprova que a imagem descomprimida é incompatível.** O script não descompacta NSO e não confere o `image_sha256` do upstream.

O relatório contém somente status e metadados. Não cole caminhos particulares, chave de console, NSO, NSP ou RomFS em PR pública. Guarde `etapa77.json` em pasta privada; não coloque o relatório no repositório por padrão.

## Testes automatizados

```sh
python3 -m unittest discover -s tests -p test_exefs_revision.py -v
cmake -S . -B build && cmake --build build && ctest --test-dir build --output-on-failure
```

O CI usa arquivos **sintéticos**, nunca os arquivos do jogo.

## Bloqueios que continuam

1. A inspeção da RomFS pela Etapa 234 listou 3.101 arquivos, mas a tentativa de extração com `unar` terminou em código 1. **RomFS não validada**.
2. Ainda não há comprovação de que os três módulos ExeFS do usuário correspondem ao perfil 1.1.0. O gate aqui criado só será executado localmente quando os arquivos estiverem disponíveis.
3. Faltam recompilação AArch64→C++, shaders e integração/link completo ao alvo PS4; o CI de plataforma até a Etapa 75 é principalmente diagnóstico e não comprova jogo rodando.

## Próximo avanço de implementação

Após confirmar a revisão ExeFS com arquivos privados, preparar o processo de geração AOT em ambiente local isolado e compilar o código gerado com OpenOrbis. Dados proprietários **não** são enviados ao GitHub. O caminho de execução só será anunciado depois de logs de link estrito e teste no console.
