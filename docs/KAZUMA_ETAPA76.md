# KAZUMA ETAPA 76 — Fechamento da pilha pública PS4 / NVN-RADV

**Data:** 12/11/2026  
**PR experimental:** #127  
**Workflow principal:** GitHub Actions run #48 — 43164399397

## Resultado

A composição pública do runtime e dos provedores PS4 agora compila e passa pelas auditorias de fechamento público.

- 87 fontes C++ únicas do runtime upstream fixado em `4043f21bb4f656d34cd17ba070238c7728d00631`, mais `games/castlevania/game.cpp` para metadados: **88 objetos ELF relocáveis PS4**.
- **14 objetos de provedores PS4** compilados, incluindo memória, controle, display, áudio, IO, configuração, relógio/threads, nome de thread, serviços opcionais, `orbis_sysconf`, `__cxa_thread_atexit_impl`, registro de módulos e entrada `main -> nx::boot()`.
- O objeto combinado ELF64 contém o carregador Vulkan oficial, os três pontos de entrada ICD reais do Mesa/RADV e o arquivo RADV real, além do zlib pareado.
- O gate da pilha pública exige 39 definições e terminou com zero provedores ausentes/duplicados, zero provedores públicos ainda indefinidos e zero imports reais exigidos ausentes.
- O gate de boot/runtime continua marcando as dependências públicas requeridas como presentes.
- O inventário de provedores do SDK encontrou 455 de 458 imports fortes com provedores reais nas bibliotecas do OpenOrbis; os três sem provedor são exatamente os módulos privados AOT esperados.

## Link estrito

O linker OpenOrbis foi executado de verdade, com saída fixa em `/dev/null`, sem gravar ELF. O resultado bruto ficou bloqueado somente pelas três referências privadas:

- `nx_module_main`
- `nx_module_sdk`
- `nx_module_subsdk0`

O novo classificador verificou que o conjunto completo de erros indefinidos é exatamente esse trio; não há bibliotecas ausentes, símbolos duplicados nem outros erros de linker. Resultado: **`PUBLIC_LINK_CLOSED_AOT_PENDING`**.

Isso significa que a composição pública está fechada para o conjunto testado. **Não significa que o link executável passou.** As três tabelas AOT verdadeiras precisam entrar somente no ambiente privado/local do projeto; não são stubs e não devem ser publicadas no GitHub.

## Correções importantes nesta etapa

1. `orbis_sysconf` encaminha para o `sysconf` real da libc. Assim, consultas como `_SC_PAGESIZE` continuam dinâmicas; não há tamanho de página presumido.
2. `__cxa_thread_atexit_impl` registra destrutores `thread_local` em chaves TSD reais do pthread e os executa em ordem inversa de registro quando a thread trabalhadora termina. A limitação documentada é que o TSD POSIX não executa destrutores da thread inicial quando o processo sai.
3. O workflow contém testes host para o encaminhamento de `sysconf` e a ordem LIFO do destrutor TLS.
4. O manifesto de compilação impede que fontes fora da lista revisada entrem no conjunto de provedores por acidente.

## Limites explícitos

- O status RADV é `PASS_PARTIAL_RADV`: o archive real e o loader foram unidos ao ELF relocável, e os três símbolos ICD estão definidos.
- Vulkan não foi inicializado no PS4; não há evidência de VkDevice, queue, swapchain, shader, draw, flip ou frame apresentado.
- O AOT privado `main/sdk/subsdk0`, ExeFS/RomFS, SPIR-V do jogo e recursos comerciais não estão incluídos.
- Esta etapa não produziu EBOOT/PKG do Castlevania, não instalou nada e não testou gameplay no console.
- Nenhum arquivo comercial foi enviado ao GitHub e nenhum byte foi escrito no Google Drive.

## Próxima etapa

Integrar as tabelas AOT verdadeiras e os recursos compatíveis em ambiente privado/local, confirmar a revisão de jogo correspondente e então fazer um link executável controlado. Só depois disso avançar para EBOOT/PKG e teste real no PS4. Não mascarar erros e não promover o status de port jogável antes de um boot verificável.
