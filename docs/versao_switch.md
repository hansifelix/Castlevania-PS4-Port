# Auditoria da versão Switch — 19/10/2026

## Evidência DISPONÍVEL: imagem da listagem do ZIP, não os arquivos NSP

Na captura fornecida, o arquivo `Castlevania.zip` contém arquivos que parecem ser:

| Item visível | Title ID no nome | Versão no nome | Tamanho aparente |
| --- | --- | --- | --- |
| Base | `0100BA4026E94000` | `v0` | 534,36 MB |
| Atualização | `0100BA4026E94800` | `v65536` (1.1.0 anunciada) | 2,96 GB |
| DLC | `0100BA4026E95001` | `v0` | 103,64 KB |

**Atenção:** a lista do site mostrada anteriormente apresentava o *base game* com
~2,96 GB e o update com ~534 MB, mas os NOMES e TAMANHOS no ZIP aparecem invertidos.
Os IDs são compatíveis com base (+0) e atualização (+0x800); isso, sozinho,
não valida os conteúdos nem prova que os arquivos foram trocados ou corrompidos.

`prod.keys` e `title.keys` também aparecem no ZIP. NUNCA envie, compartilhe,
publique ou anexe essas chaves ao relatório ou ao projeto.

## Limites do diagnóstico atual

O NSP e o ZIP de múltiplos gigabytes NÃO foram enviados ao ambiente desta análise.
Só há capturas de tela. Portanto, **não foram verificadas a integridade PFS0,
as entradas NCA, assinaturas, compatibilidade da atualização nem hashes**.

O script `tools/audit_switch.py` funciona com o `.nsp` ou `.zip` local em modo
somente-leitura. Ele apenas confere estrutura de contêiner e metadados, sem
extrair/decriptar dados. Um PFS0 íntegro não comprova que o jogo funciona.

### Uso no Galaxy A73 (Termux + Python)

Descompacte **apenas este pacote de desenvolvimento** em `Download`, sem mexer no
ZIP do jogo. Se ainda não tiver Python, no Termux rode `pkg install python`.
Permita ao Termux acesso à pasta compartilhada com `termux-setup-storage`.
Depois, ajuste os caminhos conforme o diretório escolhido:

```sh
python "$HOME/storage/downloads/Castlevania_PS4_Dev_v0.2/tools/audit_switch.py" \
  "$HOME/storage/downloads/Pasta/Castlevania.zip"
```

Copie para a conversa apenas o resultado de texto (não anexe `prod.keys`,
`title.keys` nem NSPs). O script NÃO lê o conteúdo dessas chaves.

### Verificação mínima da versão do jogo

- `v0` sinaliza pacote base, não prova atualização 1.0.0.
- `v65536` é versão interna da atualização, apresentada na página como 1.1.0.
- Diferentes jogos usam regras de versionamento específicas. Confirmar arquivos
  reais é necessário antes de prometer compatibilidade com uma recompilação.

## Atualização após teste real (19/10/2026)

O teste Termux, **feito no aparelho do usuário**, identificou o ZIP com 6
entradas e as 3 estruturas PFS0 com limites internos coerentes. Tamanhos
relatados em bytes: base `560321310`, atualização `3182299415`, DLC `106128`.
O diagnóstico acima era anterior ao teste real e está preservado como registro.
Ainda faltam validação criptográfica e confronto de Build ID/versão do código
para a recompilação macOS 1.1.0.
