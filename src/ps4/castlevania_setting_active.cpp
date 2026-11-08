// Kazuma Traducoes: PS4 adaptation of the actual Castlevania settings hook.
// Based on SwonDev/cstlvnia-blmont-to-macos (MIT), pinned at
// 4043f21bb4f656d34cd17ba070238c7728d00631, games/castlevania/video_options.cpp.
// Uses the original managed-string layout and delegates all unrelated keys.
#include <nx/runtime.h>
#include <cstdint>
#include <string_view>

namespace {
bool key_is(uint64_t text, std::u16string_view key) {
    if (!text || nx::ld<int32_t>(text + 16) != static_cast<int32_t>(key.size()))
        return false;
    for (size_t n = 0; n < key.size(); ++n)
        if (nx::ld<char16_t>(text + 20 + 2 * n) != key[n])
            return false;
    return true;
}
}

void nx_castlevania_setting_active(nx::CPU& cpu, void (*original)(nx::CPU&)) {
    // Exact upstream AOT ABI: x0 = this, x1 = managed setting key.
    if (key_is(cpu.x[1], u"video/windowmode") ||
        key_is(cpu.x[1], u"video/resolution")) {
        cpu.x[0] = 1;
        return;
    }
    // Never fabricate an answer for a non-video option or absent original.
    if (!original)
        nx::fatal("Castlevania PS4: IsSettingActive original function absent");
    original(cpu);
}
