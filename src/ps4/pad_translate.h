#pragma once
#include <cstdint>
#include "platform.h"  // Upstream MIT: runtime/src/platform.h

namespace cvps4 {
struct RawPad {
    uint32_t buttons = 0;
    uint8_t lx = 128, ly = 128, rx = 128, ry = 128;
    bool connected = false;
};

// Converts DS4's bitmask and stick axes into Horizon's Npad state.
// A/B refer to PHYSICAL EAST/SOUTH buttons, not Sony's glyphs.
nx::plat::PadState convert_pad(const RawPad& in);
}
