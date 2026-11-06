# Kazuma — Etapa 86: link parcial REAL dos 73 objetos subsdk0

## Resultado efetivamente testado em 06/11/2026 (ambiente privado)

Após Etapa 85 ter compilado todos os 73 arquivos `code_*.o` no Colab com OpenOrbis v0.5.4 + `clang++-18`, os dez lotes de backup no Google Drive foram recuperados e **verificados byte a byte** contra os seus manifests SHA-256. Todos os objetos são ELF64 relocáveis de arquitetura x86-64. Não foi necessário refazer nenhum arquivo C++ nem alterar o backup original.

- **73/73** objetos verificados, nenhum duplicado ou ausente.
- **60.067.408 bytes** de objetos antes do link.
- Comando privado `ld.lld -m elf_x86_64 -r -o subsdk0_partial_link.o code_000.o ... code_072.o`: **status 0**, nenhuma mensagem de erro.
- Objeto relocável combinado: **59.286.112 bytes**.
- Restam **6 símbolos externos**: `nx::call`, `nx::unimpl`, `ceil`, `floor`, `fma`, `trunc`. As duas funções `nx` pertencem ao runtime; as quatro outras devem ser fornecidas pela biblioteca matemática apropriada durante o link completo.
- A compilação da Etapa 85 usou correção TEMPORÁRIA de `std::countl_zero` em cópias de 14 fontes; o código original no Drive foi preservado.
- Este teste **não** foi feito com o runtime, as tabelas e os objetos de `sdk` e `main`; portanto não resulta em jogo iniciável, `eboot.bin` nem PKG.

## Reproduzir em ambiente privado

Na raiz de checkout público, usar Python 3.10+, `nm` e `ld.lld`. Colocar os dez `*objetos_privados.tar.gz` baixados do **Drive privado** numa pasta privada fora do GitHub:

```sh
python3 tools/etapa86/link_subsdk0_private.py /caminho/privado/backups \
  --report /caminho/privado/etapa86.json
```

A ferramenta verifica cada SHA-256 no manifest, a origem da Etapa 85, arquitetura ELF64 x86-64 e a presença de todos os 73 objetos. Extrai, executa o link parcial e inspeciona imports **dentro de uma pasta temporária apagada automaticamente**. A saída persistente contém somente metadados. Não publica `*.o`, código comercial ou identificadores pessoais.

Os testes automatizados `tests/test_etapa86_partial_link.py` usam dois objetos C artificiais criados com `cc`, nunca arquivos do jogo.

## Próximos bloqueios

1. Integrar tabelas `table.cpp` do AOT e implementar/resolver funções necessárias no runtime PS4 (especialmente `nx::call`, `nx::unimpl` e libm).
2. Auditar efeitos dos 321 traps estáticos em `subsdk0` — a existência estática não comprova que serão alcançados no gameplay.
3. Compilar e linkar `sdk` e `main` e verificar acessos ao guest, exceções, entradas importadas.
4. Traduzir shaders NVN→SPIR-V e integrar serviços do console e renderização.
5. Só depois, quando o link estrito e o boot realmente passarem, gerar PKG de jogo.

A marca do trabalho de port **Kazuma Traduções** permanece identificada nos arquivos próprios do projeto, sem reivindicação da autoria do jogo original.
