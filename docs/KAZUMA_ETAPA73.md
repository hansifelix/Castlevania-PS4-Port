# Kazuma 73 — Entrada e Vulkan do runtime público PS4

**Novo foco:** integrar ao *objeto real* `nx::boot()` quatro funções de plataforma (`read_pad`, GIPA, extensão e criação de surface), reutilizando contratos publicados do PS4 (etapas 62/68/69). Não acrescenta desenho de objetos, minijogo nem triângulo.

## Limites verificáveis

- Build usa OpenOrbis + Vulkan-Headers reais; o mock de controle NÃO é usado no build de PS4.
- `vkGetInstanceProcAddr` fica como import a resolver pelo bundle real Mesa/RADV/vkloader da Etapa 68.1. O workflow de link estrito sem bundle pode falhar; o relatório registra isso, não mascara o erro.
- `scePadReadState` retorna amostra do DS4. O mapeamento dos botões é Nintendo layout (círculo=A, cruz=B); touchpad provisoriamente corresponde a Minus. Sem controle/conexão retorna estado neutro.
- O backend de Pad não foi testado fisicamente neste pacote, apenas o compilador OpenOrbis e teste do mapeamento Linux quando o Actions passar.
- Nenhum conteúdo comercial, ExeFS, RomFS, AOT, PKG nem fase jogável é gerado.
- **Ainda faltam** janela/videoout do runtime (que deve trabalhar com headless WSI validado), áudio, port completo e recompilação AOT.

## Evidências exigidas

`relatorios/etapa73/LEIA_PRIMEIRO.txt`, `RELATORIO.json`, `LINK_ESTRITO.log` e `COMPILACAO.log` em artifact do workflow. Verde significa diagnóstico integrado, não que o jogo roda.
