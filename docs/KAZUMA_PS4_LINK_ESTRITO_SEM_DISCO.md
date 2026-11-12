# Operação Castlevania — diagnóstico estrito sem gravar ELF

A ferramenta tools/link/strict_link_no_storage.py executa o linker
OpenOrbis sobre objetos que já existem, com saída fixa em /dev/null.
Não cria ELF combinado, EBOOT, PKG, relatório binário ou arquivo no Drive.

## Uso

Para um objeto existente:

python3 tools/link/strict_link_no_storage.py \
  --sdk /caminho/para/openorbis \
  --object /caminho/para/objeto.o \
  --error-limit 100 \
  --extra-lib SceGnmDriver

Pode-se repetir --object e --extra-lib. Os nomes de bibliotecas extras
são validados como basenames simples; não aceitam flags ou caminhos.
O limite de mensagens permitido é 1..100. O relatório mostra contagens
e até oito exemplos por categoria, mas o próprio linker pode truncar
o diagnóstico.

## Resultado público atual

A PR draft #127 usa esta ferramenta somente na fatia NVN + vkloader +
Mesa/RADV do runner. Actions #42609853444 retornou BLOCKED com 100
símbolos indefinidos, zero bibliotecas ausentes e um aviso de limite
de erros. Os primeiros nomes são nx::game/nx::nvn/nx::log, porque
aquela fatia não contém o conjunto completo de runtime público.

Isso não é um diagnóstico do ELF AOT privado completo e não prova
que o jogo falhou no link final. Também não pode ser tratado como
link estrito aprovado. O workflow fica vermelho enquanto o link
estrito dessa lista de objetos estiver bloqueado.

## Interpretação

- BLOCKED: a lista exata de objetos/bibliotecas não fechou.
- PASS_DRYRUN: o linker aceitou somente essa lista e escreveu em
  /dev/null; não há ELF salvo nem validação de formato.
- ERROR: ferramenta, entrada, SDK ou timeout; não tratar como falha do jogo.

Nenhum dado comercial, AOT, ROMFS, ExeFS ou shader do jogo é necessário
para esta medição pública. O Google Drive não é usado.
