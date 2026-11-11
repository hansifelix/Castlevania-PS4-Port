# Lingshu — diagnóstico real PS4 em PKG: gerado, não testado no console

Data: **29 de outubro de 2026**. Objetivo: medir a disponibilidade de `sceKernelReserveVirtualRange` e `sceKernelMunmap` no PS4 com um **homebrew de diagnóstico independente**. NÃO é o Castlevania.

## Prova verificada de compilação e empacotamento

- Run GitHub Actions público: [40894283975](https://github.com/hansifelix/Castlevania-PS4-Port/actions/runs/40894283975), conclusão `success`, commit `8378f888b3cc3508949909af2f093f0a652e1214`.
- Código: `tools/lingshu-native-ps4/native_api_console.cpp`, `native_reserve_ps4_bridge.cpp`, `native_reserve_policy.h`. Sem ROM, NSP, dados originais, AOT comercial, firmware do jogo ou chaves.
- Compilação x86_64-pc-freebsd12-elf e link de ELF nativo: concluídos no job.
- Conversão do ELF via OpenOrbis `create-fself` para `eboot.bin`: concluída.
- EBOOT: **1.229.664 bytes**.
- Empacotamento `make-pkg.sh` do `orbis-ports/orbis-porting-kit` fixado no commit `213b0c38ff25ea7ca402c8844a6494086d0f1cae`, usando ferramentas do OpenOrbis v0.5.4 verificadas pelo SHA-256 de download e bibliotecas de compatibilidade na máquina efêmera do CI.
- PKG final: `IV0000-KAZM19000_00-LINGSHU190NATIVE.pkg`, **6.619.136 bytes**, gerado no runner e conferido `test -s`, manifesto `find`, `sha256sum`.
- Artefato GitHub (ZIP que contém o PKG e checksum): [LINGSHU-190-NATIVE-MEMORY-PS4-PKG-NO-GAME](https://github.com/hansifelix/Castlevania-PS4-Port/actions/runs/40894283975/artifacts/12905812709). Retenção inicial 7 dias. ZIP compactado não é PKG e deve ser extraído.
- Resultado exato registrado no log do CI:
```text
LINGSHU_DIAGNOSTIC_EBOOT_BYTES=1229664
LINGSHU_DIAGNOSTIC_EBOOT=CREATED_NOT_PKG_NOT_TESTED_ON_PS4
LINGSHU190_DIAGNOSTIC_PKG_BYTES=6619136
LINGSHU190_PKG=BUILT_OFFLINE_NO_GAME_NOT_TESTED_PS4
```

## Limite da conclusão

**O GitHub compilou e empacotou**, mas esse PKG **ainda não foi instalado nem executado no PS4 real**. Só testar no console (e resgatar o arquivo de log) dirá se a API de reserva/liberação funciona nesse firmware. Nem mesmo uma execução completa do diagnóstico demonstra que as enormes reservas de 4, 6 e 64 GiB necessárias ao runtime do jogo funcionarão. O jogo ainda não tem engine bootada ou gameplay comprovada.

## Roteiro de teste conservador no PS4 (ação manual, opcional)

1. Baixe o artefato acima no GitHub e **extraia o ZIP** no celular ou computador; o arquivo instalável é o `.pkg`, não o ZIP nem o `eboot.bin` avulso.
2. Confira que o título/ID é apenas `KAZM19000`, um diagnóstico, e que o tamanho do PKG extraído é `6619136` bytes. Não confunda com qualquer PKG comercial.
3. Se decidir testar, use apenas o método de instalação de PKG homebrew que já funciona no seu PS4 GoldHEN. Não altere configurações do sistema para este teste. Como usa APIs de memória nativa experimentais, interrompa se houver comportamento anormal, travamento ou reinicialização.
4. O programa testa **somente blocos de 16 KiB, 1 MiB e 16 MiB** por vez; após cada reserva bem-sucedida tenta liberá-la. Se não consegue limpar, interrompe novas tentativas.
5. Recuperar por FTP, **se houver gravado**, o arquivo:
   - `/data/lingshu190-native-virtual-range.log`
   - `/user/data/lingshu190-native-virtual-range.log`
   - `/mnt/usb0/lingshu190-native-virtual-range.log`
6. Procure `LINGSHU188_SUMMARY`, `LINGSHU187_RESULT` e códigos `native_rc`/`release_rc`. A existência de linhas `EXACT_RELEASED` é evidência só da reserva **pequena**; nunca inferir sucesso do jogo. A ausência de log pode significar restrição de gravação e não prova que o teste passou.
7. Não envie dados pessoais nem chaves; somente o log técnico do diagnóstico.

**Estado confirmado:** `NATIVE_PS4_DIAGNOSTIC_PKG=BUILT_CI`; `INSTALLED=NO_EVIDENCE`; `RESERVE_EXACT_PS4=UNTESTED`; `GAME_BOOT=UNTESTED`; `PLAYABLE=NO`.
