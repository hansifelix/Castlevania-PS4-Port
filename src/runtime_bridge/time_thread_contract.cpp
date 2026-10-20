#include "runtime_bridge/time_thread_contract.hpp"
#include <limits>

namespace castlevania_ps4 {

std::uint64_t MonotonicFloor::observe(std::uint64_t raw_ns) noexcept {
    auto seen = last_ns_.load(std::memory_order_acquire);
    // Nunca abaixa o ultimo tempo publicado; CAS seguro entre threads.
    while (seen < raw_ns) {
        if (last_ns_.compare_exchange_weak(seen, raw_ns,
                                           std::memory_order_acq_rel,
                                           std::memory_order_acquire)) {
            return raw_ns;
        }
    }
    return seen;
}

std::uint64_t milliseconds_to_ns_saturated(std::uint64_t ms) noexcept {
    constexpr std::uint64_t factor = 1000000;
    constexpr auto maximum = std::numeric_limits<std::uint64_t>::max();
    return ms > maximum / factor ? maximum : ms * factor;
}

std::uint64_t host_steady_clock_ns() noexcept {
    const auto elapsed = std::chrono::steady_clock::now().time_since_epoch();
    const auto raw = std::chrono::duration_cast<std::chrono::nanoseconds>(elapsed).count();
    return raw > 0 ? static_cast<std::uint64_t>(raw) : 0;
}

void OneShotSignal::signal() {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        fired_ = true;
    }
    condition_.notify_all();
}

bool OneShotSignal::is_signaled() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return fired_;
}

bool OneShotSignal::wait_for(std::chrono::milliseconds timeout) {
    std::unique_lock<std::mutex> lock(mutex_);
    // wait_for com predicado nao perde notify entre leitura e bloqueio.
    return condition_.wait_for(lock, timeout, [this] { return fired_; });
}

} // namespace castlevania_ps4
