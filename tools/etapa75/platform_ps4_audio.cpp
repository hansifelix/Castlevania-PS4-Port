// Kazuma Etapa 75 — adaptação SÍNCRONA das 3 APIs de audio do nx::plat.
// Sem música comercial, jogo ou áudio simulado na compilação OpenOrbis.
// Política explícita: um submit por vez; não alegar fila assíncrona.
#include <orbis/AudioOut.h>
#include <orbis/_types/user.h>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace nx::plat {
using AudioDone = void (*)(void*);
namespace {
constexpr size_t kFrames = 256;
constexpr size_t kFrameBytes = 2 * sizeof(int16_t);
constexpr size_t kBufferBytes = kFrames * kFrameBytes;
std::atomic<int> g_port{0};
std::atomic<unsigned> g_in_flight{0};
std::atomic<AudioDone> g_done{nullptr};
std::atomic_flag g_busy = ATOMIC_FLAG_INIT;
struct Unlock {
    ~Unlock() { g_busy.clear(std::memory_order_release); }
};
}

bool audio_open(AudioDone done) {
    if (g_busy.test_and_set(std::memory_order_acquire)) return false;
    Unlock unlock;
    if (g_port.load(std::memory_order_relaxed) > 0) {
        g_done.store(done, std::memory_order_release);
        return true;
    }
    // Chamada única, usando o contrato do exemplo OpenOrbis audio-wav.
    if (sceAudioOutInit() != 0) return false;
    const int port = sceAudioOutOpen(ORBIS_USER_SERVICE_USER_ID_SYSTEM,
        ORBIS_AUDIO_OUT_PORT_TYPE_MAIN, 0, static_cast<uint32_t>(kFrames),
        48000, ORBIS_AUDIO_OUT_PARAM_FORMAT_S16_STEREO);
    if (port <= 0) return false;
    g_done.store(done, std::memory_order_release);
    g_port.store(port, std::memory_order_release);
    return true;
}

bool audio_submit(const void* data, size_t bytes, void* ctx) {
    const int port = g_port.load(std::memory_order_acquire);
    if (port <= 0 || (bytes > 0 && data == nullptr) || (bytes % kFrameBytes != 0))
        return false;
    // Não bloquear CPU esperando outro produtor: sinalizar backpressure.
    if (g_busy.test_and_set(std::memory_order_acquire)) return false;
    g_in_flight.store(1, std::memory_order_release);
    const auto* cursor = static_cast<const uint8_t*>(data);
    size_t remaining = bytes;
    alignas(16) uint8_t chunk[kBufferBytes];
    bool ok = true;
    while (remaining > 0) {
        const size_t n = remaining < kBufferBytes ? remaining : kBufferBytes;
        std::memset(chunk, 0, sizeof(chunk));
        std::memcpy(chunk, cursor, n);
        // Tamanho fixo 256 frames e 48kHz, formato S16 estéreo.
        if (sceAudioOutOutput(port, chunk) < 0) { ok = false; break; }
        cursor += n;
        remaining -= n;
    }
    // NULL aguarda a conclusão do último bloco segundo os exemplos OpenOrbis.
    // Não podemos avisar o dono do buffer antes de concluir a operação.
    if (ok && bytes != 0 && sceAudioOutOutput(port, nullptr) < 0) ok = false;
    g_in_flight.store(0, std::memory_order_release);
    // audio_submit é síncrona nesta etapa (pode bloquear o chamador).
    // Callback ocorre no mesmo thread após liberar o lock, e só em sucesso.
    g_busy.clear(std::memory_order_release);
    if (ok) {
        auto done = g_done.load(std::memory_order_acquire);
        if (done) done(ctx);
    }
    return ok;
}

uint32_t audio_queued() {
    // 0 após retorno bem-sucedido; 1 enquanto há submit bloqueante.
    return g_in_flight.load(std::memory_order_acquire);
}
} // namespace nx::plat
