#pragma once
#include <cstdint>
#include <limits>

// Conversao sem __int128 (evita dependencia de builtins de divisao 128-bit no PS4).
namespace kazuma47 {
constexpr uint64_t billion = 1000000000ull;
inline uint64_t ticks_to_ns(uint64_t ticks, uint64_t freq) {
    if (freq == 0 || freq > (std::numeric_limits<uint64_t>::max() / billion)) return 0;
    const uint64_t seconds = ticks / freq;
    const uint64_t rem = ticks % freq;
    if (seconds > std::numeric_limits<uint64_t>::max() / billion) return 0;
    return seconds*billion + rem*billion/freq;
}
inline uint64_t round_ns_to_us(uint64_t ns) {
    return ns/1000 + (ns%1000 ? 1 : 0);
}
}
