# Kazuma Etapa 75 — AudioOut para runtime público PS4

**Não é o jogo.** Completa os três símbolos `nx::plat::audio_open`,
`nx::plat::audio_submit` e `nx::plat::audio_queued` com chamadas reais
`sceAudioOut*` do OpenOrbis, alinhado ao exemplo oficial `samples/audio-wav`.

O backend é **síncrono e experimental**, não tenta simular uma fila assíncrona:

- PCM intercalado, estéreo assinado 16-bit, 48 kHz.
- Envia quadros fixos de 256 frames (1024 bytes); último quadro é completado com silêncio.
- `audio_submit()` pode bloquear chamador; callback é invocado após `sceAudioOutOutput(handle, nullptr)`.
- `audio_queued()` expõe 1 enquanto operação bloqueante existe e 0 após.
- Reentrada concorrente durante envio retorna `false` como backpressure.
- Erro na inicialização/saída é retornado como `false`. Não inventa som.
- **Limitação**: a semântica temporal, a latência, o callback e o buffering **não foram validados num PS4 real**. Pendente teste de hardware e possível migração a fila com thread.

O CI contém testes Linux com mock declarado. A compilação OpenOrbis cruzada
usa o cabeçalho oficial `<orbis/AudioOut.h>`, jamais o mock. Tenta `ld.lld -r`
e também **link estrito** com `-lSceAudioOut`. O check verde só indica que
a integração foi auditada; não significa executável do jogo.

Após PR 75: inspecionar o `RELATORIO.json` e o `LINK_ESTRITO.log`.
Ainda faltam os módulos AOT do jogo (provenientes de ExeFS descriptografado
`main`, `sdk`, `subsdk0`) e recursos da RomFS na versão compatível.
**Jamais publicar ROMs, chaves, módulos NSO ou recursos do jogo em PR pública.**

Nota: o cabeçalho OpenOrbis define `sceAudioOutInit`, `sceAudioOutOpen` e
`sceAudioOutOutput`; o exemplo `samples/audio-wav/audio-wav/main.cpp`
é o ponto de partida para essa implementação.
