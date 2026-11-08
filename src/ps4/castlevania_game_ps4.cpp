// Kazuma Traducoes: PS4-specific game hooks for the public nx runtime.
// Adapted from SwonDev games/castlevania/game.cpp (MIT) at pinned commit
// 4043f21bb4f656d34cd17ba070238c7728d00631.
// Use INSTEAD of that game.cpp in the PS4 build; never link both providers.
#include <nx/game.h>
#include "platform.h"
#include "castlevania_resolution.hpp"
#include <cstdint>

// Exact signature in the public nx/runtime.h. No CPU dependency is needed here.
namespace nx { [[noreturn]] void fatal(const char*, ...); }

namespace nx {
const game::Info game::kInfo = {
    "castlevania", "Castlevania: Belmont's Curse", 0x0100BA4026E94000ull,
    "dev.swondev.castlevania", "private/castlevania", 0x1000000,
    true, true, true, true,
};

void game::after_init() {
    // runtime/src/main.cpp calls after_init AFTER module constructors,
    // BEFORE nnMain. Query actual SceVideoOut via nx::plat::screen_size.
    // Never invent a native 1080p window when VideoOut is unavailable.
    uint32_t width = 0, height = 0;
    plat::screen_size(width, height);
    if (!kazuma::ps4::video::configure_native(width, height)) {
        fatal("Castlevania PS4: VideoOut missing or unsupported resolution (%ux%u)",
              unsigned(width), unsigned(height));
    }
}

// The renderer remains incomplete: do not pretend these callbacks present frames.
void game::renderer_start() {}
void game::first_frame() {}
} // namespace nx
