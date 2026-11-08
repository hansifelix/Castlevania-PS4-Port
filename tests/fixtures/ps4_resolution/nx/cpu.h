#pragma once
// Synthetic CPU layout for host unit tests only. Not a Switch/PS4 SDK file.
#include <cstdint>
namespace nx {
struct CPU { std::uint64_t x[32]{}; };
[[noreturn]] void unimpl(CPU&, std::uint64_t, const char*);
}
