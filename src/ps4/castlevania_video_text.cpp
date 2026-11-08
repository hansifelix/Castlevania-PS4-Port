// Kazuma Traducoes: PS4 port of Castlevania's managed video-text hook.
// Adapted from the pinned MIT upstream's games/castlevania/video_options.cpp:
// 4043f21bb4f656d34cd17ba070238c7728d00631
// Uses the game's original managed string allocator. No fake UTF-16 pointer.
#include <nx/runtime.h>
#include "castlevania_resolution.hpp"
#include <cstdint>
#include <string>
#include <string_view>

namespace {
bool key_is(uint64_t text, std::u16string_view value) {
    if (!text || nx::ld<int32_t>(text + 16) != static_cast<int32_t>(value.size()))
        return false;
    for (size_t i = 0; i < value.size(); ++i)
        if (nx::ld<char16_t>(text + 20 + i * 2) != value[i]) return false;
    return true;
}
bool legacy_native_label(uint64_t text) {
    if (!text) return false;
    const int32_t len = nx::ld<int32_t>(text + 16);
    if (len < 9 || len > 15) return false;
    constexpr std::u16string_view expected = u"3840x2160";
    size_t pos = 0;
    for (int32_t i = 0; i < len; ++i) {
        char16_t ch = nx::ld<char16_t>(text + 20 + 2 * i);
        if (ch == u' ' || ch == u'\u00a0' || ch == u'\u202f') continue;
        if (ch == u'\u00d7' || ch == u'X') ch = u'x';
        if (pos >= expected.size() || ch != expected[pos++]) return false;
    }
    return pos == expected.size();
}
uint64_t managed_label(nx::CPU& caller, uint64_t current,
                       std::u16string_view new_label) {
    if (key_is(current, new_label)) return current;
    nx::CPU temp = caller;
    temp.x[0] = new_label.size();
    temp.x[1] = 0;
    // System.String.FastAllocateString in this pinned game's guest runtime.
    nx::call(temp, NX_BASE + 0x418f160ull);
    if (!temp.x[0] ||
        nx::ld<int32_t>(temp.x[0] + 16) != static_cast<int32_t>(new_label.size()))
        return current;
    for (size_t i = 0; i < new_label.size(); ++i)
        nx::st<char16_t>(temp.x[0] + 20 + i * 2, new_label[i]);
    return temp.x[0];
}
} // namespace

void nx_castlevania_video_text(nx::CPU& cpu, void (*original)(nx::CPU&)) {
    if (!original)
        nx::fatal("Castlevania PS4: video text original function absent");
    if (cpu.x[0] && legacy_native_label(cpu.x[1])) {
        if (!kazuma::ps4::video::ready())
            nx::fatal("Castlevania PS4: video text requires initialized VideoOut");
        uint32_t width = 0, height = 0;
        kazuma::ps4::video::native_size(width, height);
        if (width != 3840 || height != 2160) {
            const std::string text = std::to_string(width) + " x " +
                                     std::to_string(height);
            std::u16string label(text.begin(), text.end());
            label[text.find('x')] = u'\u00d7';
            const uint64_t assigned = nx::ld<uint64_t>(cpu.x[0] + 0xd8);
            cpu.x[1] = managed_label(cpu, assigned, label);
        }
    }
    original(cpu);
}
