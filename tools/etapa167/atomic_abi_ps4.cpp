// Lingshu etapa 167: prototype GNU generic atomic ABI, 16-byte aligned objects only.
// Independent from game assets; not a substitute for a validated PS4 libatomic.
// Requires x86-64 CPU with CMPXCHG16B (PS4 Jaguar supports the instruction).
#include <stddef.h>
#include <stdint.h>
#include <string.h>

namespace {
struct alignas(16) Pair128 {
    uint64_t lo;
    uint64_t hi;
};

__attribute__((always_inline)) inline void require16(size_t size, const volatile void* address) {
    // Do not silently provide non-atomic fallback or accept misalignment.
    if (size != 16 || (reinterpret_cast<uintptr_t>(address) & 15) != 0)
        __builtin_trap();
}

__attribute__((always_inline)) inline bool cas128(volatile void* address, Pair128& expected, Pair128 desired) {
    uint64_t lo = expected.lo;
    uint64_t hi = expected.hi;
    unsigned char swapped = 0;
    // LOCK CMPXCHG16B: compare RDX:RAX; swap RCX:RBX on equality.
    // Always use a full barrier (stronger than any valid requested order).
    __asm__ __volatile__(
        "lock cmpxchg16b %1\n\t"
        "sete %0"
        : "=q"(swapped), "+m"(*reinterpret_cast<volatile Pair128*>(address)),
          "+a"(lo), "+d"(hi)
        : "b"(desired.lo), "c"(desired.hi)
        : "cc", "memory");
    expected.lo = lo;
    expected.hi = hi;
    return swapped != 0;
}
} // namespace

// Compiler builtin names may not be declared/defined directly; the asm symbol
// labels export the exact ABI names expected by GNU generic atomic calls.
extern "C" __attribute__((visibility("default")))
void lingshu_atomic_load_16_generic(size_t size, const volatile void* ptr, void* out, int model)
    __asm__("__atomic_load");
extern "C" __attribute__((visibility("default")))
bool lingshu_atomic_compare_exchange_16_generic(size_t size, volatile void* ptr,
    void* expected, const void* desired, int success_model, int failure_model)
    __asm__("__atomic_compare_exchange");

extern "C" void lingshu_atomic_load_16_generic(size_t size, const volatile void* ptr,
                                                void* out, int model) {
    (void)model; // seq_cst is valid, stronger than every valid requested load order.
    require16(size, ptr);
    Pair128 expected{0, 0};
    const Pair128 unchanged{0, 0};
    // Atomic load via CAS: if zero, stores zero; otherwise observes RDX:RAX.
    // Important: DO NOT read *ptr with memcpy or a non-atomic 128-bit load.
    cas128(const_cast<volatile void*>(ptr), expected, unchanged);
    memcpy(out, &expected, sizeof expected);
}

extern "C" bool lingshu_atomic_compare_exchange_16_generic(size_t size,
    volatile void* ptr, void* expected, const void* desired,
    int success_model, int failure_model) {
    (void)success_model;
    (void)failure_model; // full barrier is a stronger valid ordering.
    require16(size, ptr);
    Pair128 want{};
    Pair128 replace{};
    memcpy(&want, expected, sizeof want);
    memcpy(&replace, desired, sizeof replace);
    bool ok = cas128(ptr, want, replace);
    if (!ok) memcpy(expected, &want, sizeof want); // required compare_exchange ABI
    return ok;
}


// Size-specialized GCC/Clang x86-64 ABI (different from generic size-first ABI).
// Verify with nm: GNU toolchains may request these two names for std::atomic<16B>.
extern "C" __attribute__((visibility("default")))
unsigned __int128 lingshu_atomic_load16_specialized(const volatile void* ptr, int model)
    __asm__("__atomic_load_16");
extern "C" __attribute__((visibility("default")))
bool lingshu_atomic_cas16_specialized(volatile void* ptr, void* expected,
    unsigned __int128 desired, int success_model, int failure_model)
    __asm__("__atomic_compare_exchange_16");

extern "C" unsigned __int128 lingshu_atomic_load16_specialized(const volatile void* ptr, int model) {
    (void)model;
    require16(16, ptr);
    Pair128 observed{0, 0};
    cas128(const_cast<volatile void*>(ptr), observed, Pair128{0, 0});
    return (static_cast<unsigned __int128>(observed.hi) << 64) | observed.lo;
}

extern "C" bool lingshu_atomic_cas16_specialized(volatile void* ptr, void* expected,
    unsigned __int128 desired, int success_model, int failure_model) {
    (void)success_model;
    (void)failure_model;
    require16(16, ptr);
    Pair128 current{}, requested{static_cast<uint64_t>(desired), static_cast<uint64_t>(desired >> 64)};
    memcpy(&current, expected, sizeof current);
    const bool success = cas128(ptr, current, requested);
    if (!success) memcpy(expected, &current, sizeof current);
    return success;
}
