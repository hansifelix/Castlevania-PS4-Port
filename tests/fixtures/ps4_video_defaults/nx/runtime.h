#pragma once
// TEST-ONLY guest-memory remapping. Never used by the PS4 OpenOrbis build.
#include <nx/cpu.h>
#include <cstdint>
#include <cstring>

namespace nx {
extern uint64_t test_static_usage_pointer;
template <typename T> inline T ld(uint64_t addr) {
    if (addr == NX_BASE + 0x6be3ec8ull) {
        // The real app maps the guest main module at NX_BASE.
        // Host tests redirect only the one pinned data pointer.
        addr = reinterpret_cast<uint64_t>(&test_static_usage_pointer);
    }
    T value{};
    std::memcpy(&value, reinterpret_cast<const void*>(addr), sizeof(T));
    return value;
}
template <typename T> inline void st(uint64_t addr, T value) {
    std::memcpy(reinterpret_cast<void*>(addr), &value, sizeof(T));
}
[[noreturn]] void fatal(const char*, ...);
void log(const char*, ...);
}
