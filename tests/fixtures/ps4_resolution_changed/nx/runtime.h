#pragma once
// SYNTHETIC host-only fixture; real PS4 CI includes the pinned upstream nx/cpu.h.
#include <nx/cpu.h>
#include <cstdint>
#include <cstring>
namespace nx {
extern uint64_t test_static_usage_pointer;
template<class T> inline T ld(uint64_t address) {
    // One pinned Castlevania static field location is virtualized for unit tests.
    if (address == NX_BASE + 0x6be3ec8ull)
        address = reinterpret_cast<uint64_t>(&test_static_usage_pointer);
    T result{};
    std::memcpy(&result, reinterpret_cast<const void*>(address), sizeof(T));
    return result;
}
template<class T> inline void st(uint64_t address, T value) {
    std::memcpy(reinterpret_cast<void*>(address), &value, sizeof(T));
}
void call(CPU& cpu, uint64_t target);
[[noreturn]] void fatal(const char*, ...);
void log(const char*, ...);
}
