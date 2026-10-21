# Kazuma Etapa 14 — primeira chamada de rotina PUBLICA nx (teste sintetico)

A PR #21 confirmou (em video no PS4) o Test 02 com video, controle, memoria e saida.

Esta etapa usa a funcao pura `nx::nvn::pick_gpu` publicada na revisao fixa
`4043f21bb4f656d34cd17ba070238c7728d00631` do repositorio
`SwonDev/cstlvnia-blmont-to-macos`, arquivo `runtime/src/nvn/nvn_gpu_pick.cpp`.

O exemplo passa dois *candidatos inventados* a regra e confere se ela seleciona
o discreto. Este teste NAO e enumeracao de GPU no PS4; NAO inicializa NVN,
Vulkan ou Mesa; NAO chama o menu do jogo; NAO incorpora binario do jogo.

A CI compila a funcao publica para o PS4, liga-a a um Test 03 derivado do
Test 02 e publica diagnosticos e PKG somente em caso de sucesso.

No console, a mensagem `NX RUNTIME CPU: OK` significara que a funcao pura nx
retornou o resultado esperado em hardware. Se nao instalar/rodar, registrar
o erro e nao insistir nem atualizar o PS4. O novo Title ID e `BREW91236`,
para nao substituir as versoes anteriores.

**Ainda faltam:** camada `nx::plat` para PS4, entrada e carregador do jogo,
recompilacao AArch64->C++ dos modulos do proprietario legitimamente obtidos,
graficos NVN->API disponivel no PS4, shaders, assets, audio, persistencia e
integracao. Nem este teste nem compilar objetos isolados aproxima diretamente
o menu original: sao apenas provas preliminares de infraestrutura.

Nao compartilhar ROMs, NSP/APK/NCA, chaves ou arquivos comerciais no GitHub.
A funcao publica e consumida temporariamente de fonte upstream identificada;
verificar/licenciar qualquer redistribuicao conforme o projeto de origem.
