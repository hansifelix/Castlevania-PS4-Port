// Kazuma Traducoes: PS4 provider for the real Castlevania AOT video-defaults hook.
// Adapted from games/castlevania/video_options.cpp (MIT), pinned upstream commit
// 4043f21bb4f656d34cd17ba070238c7728d00631.
// This operates on the game's original managed arrays, not on mock display options.
#include <nx/runtime.h>
#include "castlevania_resolution.hpp"
#include <cstdint>

namespace {
constexpr uint64_t kVideoSettingsUsage = NX_BASE + 0x6be3ec8ull;

uint64_t static_fields() {
    const uint64_t usage = nx::ld<uint64_t>(kVideoSettingsUsage);
    if (!usage) return 0;
    const uint64_t klass = nx::ld<uint64_t>(usage);
    return klass ? nx::ld<uint64_t>(klass + 0xb8) : 0;
}
} // namespace

void nx_castlevania_video_defaults(nx::CPU& cpu, void (*original)(nx::CPU&)) {
    // The original game fills the arrays. Alter only the verified final entry
    // after its initialization, exactly as the pinned upstream hook does.
    if (!original)
        nx::fatal("Castlevania PS4: video defaults original function absent");
    original(cpu);

    const uint64_t fields = static_fields();
    if (!fields) return;
    uint32_t width = 0, height = 0;
    kazuma::ps4::video::native_size(width, height);
    if (!kazuma::ps4::video::ready() || !width || !height)
        nx::fatal("Castlevania PS4: video defaults require initialized VideoOut");

    // Both the general list and its 16:9 list contain twelve pairs.
    // Never overwrite unrelated entries if the game's array shape differs.
    for (uint64_t offset = 0; offset <= 8; offset += 8) {
        const uint64_t resolutions = nx::ld<uint64_t>(fields + offset);
        if (!resolutions) continue;
        const uint32_t count = nx::ld<uint32_t>(resolutions + 24);
        if (count != 12) continue;
        const uint64_t tuple = resolutions + 32 + (uint64_t(count) - 1) * 8;
        nx::st<uint32_t>(tuple, width);
        nx::st<uint32_t>(tuple + 4, height);
    }
    nx::log("Castlevania PS4: native video mode %ux%u", width, height);
}
