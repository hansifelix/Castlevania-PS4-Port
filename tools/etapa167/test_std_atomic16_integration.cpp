// Lingshu 169: real std::atomic<Value> ABI integration, no game code.
// Verifies GNU/Clang size-specialized __atomic_load_16 / compare_exchange_16.
#include <atomic>
#include <cstdint>
#include <cassert>
#include <cstdio>
#include <thread>

struct alignas(16) Value { std::uint64_t lo, hi; };
static std::atomic<Value> state(Value{0, 0});

int main() {
    Value expected{0, 0};
    const Value desired{55, ~std::uint64_t(55)};
    assert(state.compare_exchange_strong(expected, desired));
    Value got = state.load();
    assert(got.lo == 55 && got.hi == ~std::uint64_t(55));

    expected = Value{0, 0};
    assert(!state.compare_exchange_strong(expected, Value{33, 44}));
    assert(expected.lo == 55 && expected.hi == ~std::uint64_t(55));

    std::atomic<bool> done{false};
    std::thread writer([&]() {
        for (std::uint64_t i = 100; i < 10000; ++i) {
            Value seen = state.load();
            while (!state.compare_exchange_weak(seen, Value{i, ~i})) {}
        }
        done.store(true, std::memory_order_release);
    });
    while (!done.load(std::memory_order_acquire)) {
        const Value observed = state.load();
        assert(observed.hi == ~observed.lo);
    }
    writer.join();
    got = state.load();
    assert(got.lo == 9999 && got.hi == ~std::uint64_t(9999));
    puts("LINGSHU169_STD_ATOMIC16_INTEGRATION=PASSED");
}
