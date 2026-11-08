#pragma once
// Synthetic layout used by host tests only. Production uses upstream nx/cpu.h.
#include <cstdint>
#ifndef NX_BASE
#define NX_BASE 0x0000004000000000ull
#endif
namespace nx {
union alignas(16) V128 { float f32[4]; uint64_t u64[2]; };
struct CPU {
    std::uint64_t x[32]{};
    V128 v[32]{};
};
[[noreturn]] void unimpl(CPU&, std::uint64_t, const char*);
}
