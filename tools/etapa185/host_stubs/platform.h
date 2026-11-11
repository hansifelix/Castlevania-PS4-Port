// Only for Linux host tests; PS4 uses the real pinned upstream platform.h.
#pragma once
#include <cstdint>
namespace nx::plat {
bool reserve(std::uint64_t addr,std::uint64_t size);
bool commit(std::uint64_t addr,std::uint64_t size);
void decommit(std::uint64_t addr,std::uint64_t size);
}
