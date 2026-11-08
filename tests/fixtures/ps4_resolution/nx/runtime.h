#pragma once
// Synthetic host unit-test API only, never part of the real OpenOrbis build.
#include <nx/cpu.h>
#include <cstdint>
#include <cstring>
namespace nx {
template <typename T> inline T ld(uint64_t addr) {
    T out{};
    std::memcpy(&out, reinterpret_cast<const void*>(addr), sizeof(T));
    return out;
}
void call(CPU& cpu, uint64_t addr);
[[noreturn]] void fatal(const char* message, ...);
void log(const char* message, ...);
}
