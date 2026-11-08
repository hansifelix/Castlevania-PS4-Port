# Operação Castlevania — diagnóstico de link real sem gastar armazenamento

**Urgência de 08/11/2026:** o usuário informou ~10 GB livres no
Google Drive e determinou que **nenhum novo arquivo ou backup** seja
enviado para lá. Esta etapa não usa o Drive, Colab, download de ROM,
AOT comercial nem cria outro ELF de gigabytes.

O AOT privado relatado no marco de 07–08/11 tem cerca de 1,75 GB no link
ELF relocável. A antiga Etapa 42 tentava o link final gravando
outro ELF intermediário, o que aumenta o consumo de disco.

A ferramenta `tools/link/strict_link_no_storage.py` usa as **mesmas**
opções essenciais do link OpenOrbis (`crt1.o`, `link.x`, libc++,
libc, libkernel e libm quando presente), e uma tentativa de `ld.lld-18
-pie --no-undefined --fatal-warnings`, com `-o /dev/null`.
O linker **processa os objetos existentes no disco**, mas **não salva**
um novo executável combinado, EBOOT, PKG ou arquivo de relatório.
O stdout é apenas um JSON pequeno com status/contagens e até oito
nomes de erros por categoria; nenhum upload é realizado.

### Execução PRIVADA, somente se o ELF combinado e o SDK já existirem

```bash
python3 tools/link/strict_link_no_storage.py \
  --sdk /caminho/para/openorbis \
  --object /caminho/privado/combined_aot_runtime.o
```

Use `--object` novamente para provedores públicos **não incluídos**
no objeto combinado. O caminho é um exemplo: **não existe** esse
arquivo no GitHub público, e esta etapa NÃO recupera nem reconstrói
o binário privado. O teste não é executado automaticamente no CI
para não gastar horas/memória e não expor material derivado do jogo.

### Como interpretar o resultado

- `BLOCKED`: link estrito real rejeitou referências, ABI ou bibliotecas.
  O diagnóstico mostra até oito exemplos para priorizar correções;
  quantidades podem ser truncadas pelo limite de erros do linker.
- `PASS_DRYRUN`: o linker retornou código zero para esta **lista
  específica de objetos e bibliotecas**. Ainda não há arquivo ELF
  para validar nem `eboot.bin`, PKG ou prova de execução no PS4.
- `ERROR`: entrada/SDK ausente, falha de ferramenta ou timeout;
  não tratar como erro do jogo.

Não confundir o link parcial `ld.lld -r` das PRs anteriores com
este diagnóstico estrito, e não falsificar símbolos.
O objetivo seguinte é analisar dependências verificadas e resolver
somente as que faltarem, antes de qualquer construção pesada.

Os testes host são sintéticos e validam especificamente o comando,
a saída `/dev/null`, a distinção entre sucesso e falha e a ausência
de produção de arquivo binário. **Este PR não inclui o teste AOT
privado e não declara link estrito do jogo aprovado.**
