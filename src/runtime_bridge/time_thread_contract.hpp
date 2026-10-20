#pragma once
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <mutex>

// Kazuma Port Games - ETAPA 3. Contratos testados SOMENTE no host.
// Nao implementa nx::plat, scePthread, sceKernel, eboot.bin nem o jogo.
namespace castlevania_ps4 {

// Uma fonte de tempo nao deve andar para tras quando observada em sequencia.
// A ordem de chamadas concorrentes e linearizada pela variavel atomica.
class MonotonicFloor {
public:
    explicit MonotonicFloor(std::uint64_t initial_ns = 0) noexcept
        : last_ns_(initial_ns) {}
    std::uint64_t observe(std::uint64_t raw_ns) noexcept;
    std::uint64_t last() const noexcept {
        return last_ns_.load(std::memory_order_acquire);
    }
private:
    std::atomic<std::uint64_t> last_ns_;
};

// Conversao segura para duracoes; saturacao em vez de overflow silencioso.
std::uint64_t milliseconds_to_ns_saturated(std::uint64_t ms) noexcept;

// Referencia nativa SOMENTE para Linux, Termux e testes de CI.
std::uint64_t host_steady_clock_ns() noexcept;

// Sinal de disparo unico: quem ja recebeu o sinal nao perde a notificacao.
// Em PS4 sera preciso um backend proprio com primitivas da plataforma.
class OneShotSignal {
public:
    void signal();
    bool is_signaled() const;
    bool wait_for(std::chrono::milliseconds timeout);
private:
    mutable std::mutex mutex_;
    std::condition_variable condition_;
    bool fired_ = false;
};

} // namespace castlevania_ps4
