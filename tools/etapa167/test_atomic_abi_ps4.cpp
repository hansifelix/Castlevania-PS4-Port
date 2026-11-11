#include <atomic>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <thread>

struct alignas(16) Pair128 { uint64_t lo, hi; };
extern "C" void load_generic(size_t size, const volatile void* p, void* out, int model)
    __asm__("__atomic_load");
extern "C" bool cas_generic(size_t size, volatile void* p, void* expected,
    const void* desired, int success_order, int failure_order)
    __asm__("__atomic_compare_exchange");

alignas(16) static Pair128 atom{0, 0};

static void check_load(uint64_t lo, uint64_t hi) {
    Pair128 v{};
    load_generic(16, &atom, &v, __ATOMIC_SEQ_CST);
    assert(v.lo == lo && v.hi == hi);
}

int main() {
    check_load(0, 0);
    Pair128 e{1, 2}, d{3, 4};
    assert(!cas_generic(16, &atom, &e, &d, __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST));
    assert(e.lo == 0 && e.hi == 0); // failed CAS updates expected
    Pair128 zero{0, 0};
    assert(cas_generic(16, &atom, &zero, &d, __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST));
    assert(zero.lo == 0 && zero.hi == 0); // successful CAS leaves expected unchanged
    check_load(3, 4);
    Pair128 n{0,0};
    assert(cas_generic(16, &atom, &d, &n, __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST));
    check_load(0, 0);

    // Concurrency: both 64-bit halves must belong to the same 128-bit snapshot.
    // Single writer updates via CAS, reader uses 16-byte atomic load.
    std::atomic<bool> done{false};
    std::thread writer([&]() {
        for (uint64_t i = 1; i < 150000; ++i) {
            Pair128 next{i, ~i};
            Pair128 prev{};
            load_generic(16, &atom, &prev, __ATOMIC_RELAXED);
            while (!cas_generic(16, &atom, &prev, &next, __ATOMIC_RELEASE, __ATOMIC_ACQUIRE)) { }
        }
        done.store(true, std::memory_order_release);
    });
    uint64_t samples = 0;
    while (!done.load(std::memory_order_acquire)) {
        Pair128 observed{};
        load_generic(16, &atom, &observed, __ATOMIC_ACQUIRE);
        if (observed.lo != 0) assert(observed.hi == ~observed.lo);
        ++samples;
    }
    writer.join();
    Pair128 final{};
    load_generic(16, &atom, &final, __ATOMIC_SEQ_CST);
    assert(final.lo == 149999 && final.hi == ~final.lo);
    printf("LINGSHU167_GENERIC_ATOMIC16_CAS_LOAD=PASSED samples=%llu\n", (unsigned long long)samples);
}
