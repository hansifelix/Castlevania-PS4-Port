# Lingshu — diagnóstico nativo de memória: ELF → EBOOT comprovado

Data: 29/10/2026. Este projeto é um diagnóstico homebrew **sem jogo**.

## Evidência de CI (não de console)

A execução GitHub Actions pública [#40893483143](https://github.com/hansifelix/Castlevania-PS4-Port/actions/runs/40893483143), no commit `088851ffa5e018c27ac60d353535c9aaf9b18286`, terminou com conclusão **success** usando runner alocado.

Concluiu estas etapas distintas:

1. Download do SDK público OpenOrbis v0.5.4 com SHA256 esperado;
2. Compilação de `native_reserve_ps4_bridge.cpp` para `x86_64-pc-freebsd12-elf`;
3. Compilação da interface de diagnóstico e do helper gráfico OpenOrbis;
4. Link final de um ELF PS4 independente, **sem material comercial**;
5. Conversão pelo `create-fself` para `eboot.bin`;
6. Upload de arquivos `eboot.bin` + `lingshu-eboot.sha256`, e, separadamente, ELF + checksum.

Trecho observado nos logs reais:
```text
LINGSHU_DIAGNOSTIC_EBOOT_BYTES=1229664
LINGSHU_DIAGNOSTIC_EBOOT=CREATED_NOT_PKG_NOT_TESTED_ON_PS4
```

Artefato de EBOOT: [LINGSHU-NATIVE-PS4-EBOOT-NOT-PKG-NO-GAME](https://github.com/hansifelix/Castlevania-PS4-Port/actions/runs/40893483143/artifacts/12904819681) (GitHub Actions, retenção de 7 dias). Arquivo ZIP de upload com 354010 bytes compactados, **não confundir** com tamanho real do EBOOT de 1229664 bytes.

Artefato de ELF: [LINGSHU-NATIVE-PS4-ELF-NOT-EBOOT-NOT-PKG](https://github.com/hansifelix/Castlevania-PS4-Port/actions/runs/40893483143/artifacts/12905751545).

## Restrições

- **EBOOT não é PKG instalável** e não deve ser instalado como se fosse um pacote PS4.
- O diagnóstico usa a ponte `sceKernelReserveVirtualRange/sceKernelMunmap`, mas **as APIs ainda não foram executadas no PS4 do usuário**, nem sequer para 16 KiB.
- Há prova de compilação e link, não prova de sucesso de reservas de memória.
- Não há ELF/EBOOT do Castlevania nesta branch e o boot do jogo continua sem comprovação.
- No PS4 real, o único dado relevante de mmap para regiões completas segue o log da etapa 181: `EINVAL=22` em 4/6/64 GiB. Isso não se resolve por construir um EBOOT isolado.
- A etapa seguinte para o diagnóstico é **empacotar em PKG homebrew genuíno** com ferramentas verificadas, obter checksum e testar no console com recuperação de log; não afirmar sucesso antes da execução.
