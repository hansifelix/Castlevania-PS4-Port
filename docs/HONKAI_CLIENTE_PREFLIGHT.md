# Projeto Alfa — Honkai: Star Rail PS4: pré-análise offline de clientes (07/11/2026)

## Teste 0: formato do cliente antes de qualquer login ou PKG

O usuário autorizou investigar a viabilidade com uma conta descartável. **Conta nova não evita a possibilidade de roubo de credenciais, APK adulterado, malware nem bloqueio de outras contas e aparelhos.** Não instalar aplicativo de origem incerta ou cadastrar credenciais em executáveis não auditados.

Esta etapa implementa uma ferramenta local **somente de leitura** para identificar o contêiner e CPU de arquivos (APK/PE/ELF), sem executá-los, instalar modificações, conectar a servidores nem contornar verificações. Nenhum cliente foi fornecido, testado ou alterado nesta etapa.

## Uso local com arquivo cuja procedência seja conhecida

```sh
python3 tools/honkai/client_preflight.py /caminho/local/cliente.apk --sha256
python3 tools/honkai/client_preflight.py /caminho/local/cliente.exe
```

Saída JSON: `format`, `architecture`, `bytes`, `sha256` (opcional), metadados não sensíveis de APK (`AndroidManifest.xml`, `classes*.dex`, arquiteturas de libs, indícios `libunity.so`/`libil2cpp.so`) e alertas sobre compatibilidade. O script apenas enumera a tabela ZIP, sem descompactar dados do jogo e sem copiar dados comerciais ao GitHub.

**Aviso crucial:** arquitetura x86-64 de um `.exe` de Windows NÃO significa que esse programa roda no PS4 x86-64. Um APK com `arm64-v8a` não vira EBOOT por mudar extensão. O script também NÃO verifica assinatura criptográfica, reputação ou se um cliente foi modificado — usa apenas observações do formato.

```sh
python3 tests/test_client_preflight.py
```

Os testes sintéticos criam APK falso, PE x86-64 sintético, ELF ARM64 sintético, ZIP não APK e rejeição de symlink. CTest automatiza a execução no GitHub Actions sem clientes reais.

## O que falta para começar *teste real de cliente*

1. Arquivo de origem autorizada/identificada, local e confiável, para classificar formato sem executá-lo.
2. Verificação independente de assinatura/sha256 e proveniência do distribuidor; nunca presumir que `libunity.so` valida segurança.
3. Avaliação de licença/regras e portabilidade de ABI, graphics, libs e autenticação.
4. Só então experimento offline isolado que tenha hipótese mensurável. **Não há port nativo, PKG, login ou gameplay.**

Referência das restrições públicas HoYoverse: https://hsr.hoyoverse.com/en-us/news/111203?type=news e https://hsr.hoyoverse.com/en-us/news/111244

Desenvolvimento no repositório público limitado a infraestrutura e arquivos de teste falsos.

## 07/11 — Auditoria real da ABI das bibliotecas nativas dentro do APK

O teste original relatava apenas **o nome da pasta** `lib/arm64-v8a`, `lib/x86_64` etc. Isso é insuficiente: o nome pode estar errado ou manipulado. Agora o inspetor lê somente o cabeçalho ELF de cada biblioteca `.so` listada no APK, compara arquitetura/classe ELF com a pasta declarada e retorna:

- `native_header_checked`, `native_header_matching`, `native_header_mismatch` e `native_header_invalid`;
- `native_library_abi_consistent` verdadeiro apenas se houver ao menos uma biblioteca e todas as bibliotecas inspecionadas forem coerentes;
- `duplicate_zip_entries` para denunciar nomes ZIP repetidos.

Arquitetura coerente **não** é prova de assinatura, segurança, origem, integridade, ausência de malware, possibilidade de rodar no PS4 ou compatibilidade de autenticação. Arquitetura suspeita é somente um sinal para parar a avaliação e examinar a procedência. Os novos testes fabricam bibliotecas ELF falsas com cabeçalhos ARM64 válidos, pastas x86-64 incoerentes e conteúdo não ELF. Nenhum APK real foi baixado ou executado.

**Próximo bloqueio:** obter um cliente legítimo, local, de fonte conhecida para produzir relatório privado. Para um cliente modificado, executar login mesmo com conta nova continua arriscando o aparelho e credenciais; esta etapa não autoriza nenhuma tentativa de burlar autenticação ou antibot.

## Etapa de segurança do próprio scanner — ZIP e hash de referência

Antes de ler qualquer biblioteca de um APK/ZIP, o inspetor rejeita:
- entradas duplicadas ou sem nome, nomes absolutos, traversal `..`, barras invertidas em caminhos e symlinks;
- membros criptografados;
- mais de 100 mil arquivos, mais de 16 GiB de tamanho descomprimido declarado, ou razão de compressão acima de 2000:1.

Esses limites são conservadores e **não constituem antivírus**. Não garantem que um APK não tenha malware, nem que a compressão não possa ter defeitos. A inspeção lê cabeçalhos de arquivos (não executa nem instala o cliente).

Para conferir **integridade de conteúdo** com uma referência SHA-256 independente e confiável:

```sh
python3 tools/honkai/client_preflight.py ./arquivo.apk --expected-sha256 HASH_HEXADECIMAL_DE_64_CARACTERES
```

Se o hash não coincidir, o programa termina com erro; se coincidir, apenas sabemos que o arquivo tem os mesmos bytes da referência — isso **não prova que a referência seja segura**. Nunca confiar num hash copiado da mesma página desconhecida que forneceu o APK sem verificar procedência. O resultado carrega `malware_free: not_evaluated` para evitar alegações enganosas.

Não instalar APK alterado em aparelho com contas principais, apps bancários e sessões pessoais. Conta de teste isolada não protege o dispositivo contra aplicação maliciosa.
