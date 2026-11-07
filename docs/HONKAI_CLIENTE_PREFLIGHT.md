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
