#pragma once
// Host-only nx::plat contract; the real PS4 provider lives at tools/etapa74.
#include <cstdint>
namespace nx::plat { void screen_size(uint32_t& width, uint32_t& height); }
