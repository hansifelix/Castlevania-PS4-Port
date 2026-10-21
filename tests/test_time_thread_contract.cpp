#include "runtime_bridge/time_thread_contract.hpp"
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <thread>
#include <vector>

using namespace castlevania_ps4;
using namespace std::chrono_literals;

// CHECK funciona mesmo com -DNDEBUG (CMake Release).
#define CHECK(condition) do { \
    if (!(condition)) { \
        std::fprintf(stderr, "FAILED %s:%d : %s\n", __FILE__, __LINE__, #condition); \
        return EXIT_FAILURE; \
    } \
} while (false)

int main() {
    MonotonicFloor clock(100);
    CHECK(clock.observe(90) == 100);
    CHECK(clock.observe(100) == 100);
    CHECK(clock.observe(150) == 150);
    CHECK(clock.observe(120) == 150);
    CHECK(clock.last() == 150);

    CHECK(milliseconds_to_ns_saturated(0) == 0);
    CHECK(milliseconds_to_ns_saturated(1) == 1000000);
    CHECK(milliseconds_to_ns_saturated(1000) == 1000000000);
    constexpr auto maximum = std::numeric_limits<std::uint64_t>::max();
    CHECK(milliseconds_to_ns_saturated(maximum) == maximum);
    CHECK(milliseconds_to_ns_saturated(maximum / 1000000) == (maximum / 1000000) * 1000000);
    CHECK(milliseconds_to_ns_saturated(maximum / 1000000 + 1) == maximum);

    const auto before = host_steady_clock_ns();
    const auto after = host_steady_clock_ns();
    CHECK(after >= before); // Nao depende de avancar de fato entre duas chamadas.

    OneShotSignal gate;
    CHECK(!gate.is_signaled());
    CHECK(!gate.wait_for(0ms)); // Tempo zero: nao bloqueia.

    std::array<bool, 2> woke{{false, false}};
    std::thread t1([&] { woke[0] = gate.wait_for(3s); });
    std::thread t2([&] { woke[1] = gate.wait_for(3s); });
    gate.signal();
    t1.join();
    t2.join();
    CHECK(woke[0] && woke[1]);
    CHECK(gate.is_signaled());
    CHECK(gate.wait_for(0ms)); // Notificacao persistente.
    gate.signal(); // Dupla sinalizacao nao altera estado.
    CHECK(gate.is_signaled());

    // Varios produtores concorrentes, o maior timestamp prevalece.
    MonotonicFloor shared;
    std::array<std::thread, 4> workers;
    for (std::size_t i = 0; i < workers.size(); ++i) {
        workers[i] = std::thread([&, i] {
            for (std::uint64_t n = 0; n < 1000; ++n) {
                (void)shared.observe((i + 1) * 1000 + n);
            }
        });
    }
    for (auto& t : workers) t.join();
    CHECK(shared.last() == 4999);
    CHECK(shared.observe(1) == 4999);

    std::puts("Kazuma runtime etapa 3: OK (tempo/thread host-only, sem PS4 e sem jogo)");
    return EXIT_SUCCESS;
}
