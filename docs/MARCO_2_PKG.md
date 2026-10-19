# Marco 2 — PKG técnico de laboratório (sem Castlevania)

**Status:** preparado para teste pelo GitHub Actions. Ainda não houve compilação/empacotamento deste marco nem validação no PS4 até que a nova Pull Request passe.

A ação `.github/workflows/ps4-pkg-lab.yml` usa o mesmo código `ps4_hello/main.cpp` cuja compilação OpenOrbis funcionou no Marco 1. O pacote gerado, se a ação completar sem erros, conterá um homebrew de espera que faz `printf` e dorme em loop. **Não roda Castlevania; não tem renderização gráfica**. É possível que na TV apareça apenas tela preta; o teste é se instala, inicia, permanece aberto e fecha normalmente via botão PS.

- Title ID de teste: `LABS10001`.
- Nome na tela: `PS4 - Teste tecnico (sem jogo)`.
- Ícone: padrão, criado por script sem imagens comerciais.
- Ferramentas: OpenOrbis 0.5.4 verificado por SHA-256 e scripts do kit `orbis-porting-kit` fixados em commit `213b0c38ff25ea7ca402c8844a6494086d0f1cae`.
- GitHub Actions utiliza Linux; o kit possui tratamento de compatibilidade OpenSSL 1.1 para o `PkgTool.Core`. Se o download de bibliotecas antigas falhar, o job falhará; **não tente instalar arquivos aleatórios no celular**. Precisaremos corrigir o workflow.
- Artefato esperado: `ps4-laboratorio-pkg-sem-jogo` em **Actions > PS4 - PKG laboratorio (sem jogo)**. É um ZIP contendo o PKG. O GitHub retém o artefato por sete dias.
- Fonte (sem ROM): `https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain`; kit empacotador (MIT + exceção declarada) `https://github.com/orbis-ports/orbis-porting-kit`.

## Teste no console, apenas depois de CI verde

1. Baixe o artefato ZIP no GitHub, extraia o `.pkg` e confirme o nome de laboratório.
2. Passe para armazenamento USB compatível ou por transferência local que você já usa no PS4.
3. Instale como homebrew de teste pelo gerenciador de PKGs do console desbloqueado.
4. Abra. Não espere menus ou imagens do Castlevania: o aplicativo apenas escreve uma mensagem nos logs e espera.
5. Se ficar aberto sem travar e puder ser fechado pelo menu do botão PS, reportar sucesso do marco. Se houver erro CE-xxxxx, anote o código e não insista.

Não use arquivos `.nsp`, `.xci`, `.keys` e `*.apk` neste marco. O primeiro PKG do laboratório não comprova possibilidade de portar o jogo. A portabilidade do Castlevania exigiria uma compilação independente dos módulos recompilados e integração de gráficos, memória, áudio e controles com bibliotecas do PS4.
