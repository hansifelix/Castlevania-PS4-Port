#pragma once
// Synthetic host fixture only; NEVER on the real OpenOrbis include path.
#include <nx/cpu.h>
#include <cstdint>
#include <cstring>
namespace nx {
template<class T> inline T ld(uint64_t addr) {
    T value{};
    std::memcpy(&value, reinterpret_cast<const void*>(addr), sizeof(T));
    return value;
}
template<class T> inline void st(uint64_t addr, T value) {
    std::memcpy(reinterpret_cast<void*>(addr), &value, sizeof(T));
}
void call(CPU& cpu, uint64_t address);
[[noreturn]] void fatal(const char*, ...);
void log(const char*, ...);
}
