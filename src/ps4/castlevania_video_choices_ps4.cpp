// Kazuma Traducoes — real Castlevania PS4 video option callbacks.
// Adapted from games/castlevania/video_options.cpp (MIT) at
// 4043f21bb4f656d34cd17ba070238c7728d00631.
// The PS4 VideoOut is fullscreen-only. No imaginary window manager.
#include <nx/runtime.h>
#include "castlevania_resolution.hpp"
#include "castlevania_video_choices.hpp"
#include <cstdint>
#include <string>
#include <string_view>

namespace {
constexpr uint64_t kVideoStaticUsage = NX_BASE + 0x6be3ec8ull;
constexpr uint32_t kFullscreenMode = 1;
uint64_t static_fields() {
    const uint64_t usage = nx::ld<uint64_t>(kVideoStaticUsage);
    if (!usage) return 0;
    const uint64_t klass = nx::ld<uint64_t>(usage);
    return klass ? nx::ld<uint64_t>(klass + 0xb8) : 0;
}
bool matching_label(uint64_t text, std::u16string_view wanted) {
    if (!text || nx::ld<int32_t>(text + 16) != static_cast<int32_t>(wanted.size()))
        return false;
    for (size_t i=0;i<wanted.size();++i)
        if (nx::ld<char16_t>(text + 20 + 2*i) != wanted[i]) return false;
    return true;
}
uint64_t managed_label(nx::CPU& caller, uint64_t existing, std::u16string_view label) {
    if (matching_label(existing, label)) return existing;
    nx::CPU temp = caller;
    temp.x[0] = label.size();
    temp.x[1] = 0;
    nx::call(temp, NX_BASE + 0x418f160ull); // Guest System.String.FastAllocateString
    if (!temp.x[0] || nx::ld<int32_t>(temp.x[0] + 16) != static_cast<int32_t>(label.size()))
        return existing;
    for (size_t i=0;i<label.size();++i)
        nx::st<char16_t>(temp.x[0] + 20 + 2*i, label[i]);
    return temp.x[0];
}
void window_choices(uint64_t window, uint64_t fields) {
    if (!window || !fields) return;
    const uint64_t modes = nx::ld<uint64_t>(fields + 0x10);
    const uint64_t choices = nx::ld<uint64_t>(window + 0x58);
    if (!modes || !choices) return;
    const uint32_t count = nx::ld<uint32_t>(choices + 24);
    if (count == 0 || count > 4 || count != nx::ld<uint32_t>(modes + 24)) return;
    for (uint32_t n=0;n<count;++n) {
        const uint64_t entry = nx::ld<uint64_t>(choices + 32 + 8*n);
        if (!entry) continue;
        const uint32_t idx = nx::ld<uint32_t>(entry + 0x20);
        if (idx >= count) continue;
        const uint32_t mode = nx::ld<uint32_t>(modes + 32 + 4*idx);
        // PS4 has no OS desktop/windowed presentation. Only fullscreen is valid.
        const bool enabled = mode == kFullscreenMode;
        nx::st<uint8_t>(entry + 0x28, static_cast<uint8_t>(enabled));
        if (enabled) nx::st<uint32_t>(window + 0x1c, idx);
    }
}
void resolution_choices(nx::CPU& caller, uint64_t setting, uint64_t fields) {
    if (!setting || !fields) return;
    const uint64_t modes = nx::ld<uint64_t>(fields);
    const uint64_t choices = nx::ld<uint64_t>(setting + 0x58);
    if (!modes || !choices) return;
    const uint32_t count = nx::ld<uint32_t>(choices + 24);
    if (count == 0 || count > 32 || count != nx::ld<uint32_t>(modes + 24)) return;
    uint32_t nw=0, nh=0, rw=0, rh=0;
    kazuma::ps4::video::native_size(nw, nh);
    kazuma::ps4::video::render_size(rw, rh);
    uint64_t seen[32]{};
    uint32_t seen_count=0;
    for (uint32_t n=0;n<count;++n) {
        const uint64_t value = nx::ld<uint64_t>(choices + 32 + 8*n);
        if (!value) continue;
        const uint32_t idx = nx::ld<uint32_t>(value + 0x20);
        if (idx >= count) continue;
        const uint64_t pair = modes + 32 + 8ull*idx;
        const uint32_t w = nx::ld<uint32_t>(pair);
        const uint32_t h = nx::ld<uint32_t>(pair + 4);
        if (idx+1 == count && w == nw && h == nh) {
            const std::string ascii = std::to_string(w) + "x" + std::to_string(h);
            const std::u16string label(ascii.begin(),ascii.end());
            nx::st<uint64_t>(value + 0x10,
                managed_label(caller, nx::ld<uint64_t>(value + 0x10), label));
        }
        const uint64_t packed = (uint64_t(w)<<32) | h;
        bool duplicate=false;
        for (uint32_t i=0;i<seen_count;++i)
            if (seen[i] == packed) { duplicate=true; break; }
        const bool allowed = nw && nh && w>=640 && h>=360 &&
            w<=nw && h<=nh && uint64_t(w)*9 == uint64_t(h)*16 && !duplicate;
        if (allowed) seen[seen_count++] = packed;
        nx::st<uint8_t>(value + 0x28, static_cast<uint8_t>(allowed));
        if (allowed && w==rw && h==rh)
            nx::st<uint32_t>(setting + 0x1c, idx);
    }
}
} // namespace

void kazuma::ps4::video::refresh_video_choices(nx::CPU& cpu, uint64_t self) {
    if (!self) return;
    const uint64_t fields = static_fields();
    if (!fields) return;
    if (!ready())
        nx::fatal("Castlevania PS4: video choices require initialized VideoOut");
    resolution_choices(cpu, nx::ld<uint64_t>(self + 0x68), fields);
    window_choices(nx::ld<uint64_t>(self + 0x58), fields);
}

void nx_castlevania_supported_resolutions(nx::CPU& cpu,
                                          void (*original)(nx::CPU&)) {
    if (!original)
        nx::fatal("Castlevania PS4: supported resolutions original absent");
    const uint64_t self = cpu.x[0];
    original(cpu); // Populate game's managed arrays before reading or altering them.
    kazuma::ps4::video::refresh_video_choices(cpu, self);
}

void nx_castlevania_fullscreen_mode(nx::CPU& cpu, void (*)(nx::CPU&)) {
    if (!kazuma::ps4::video::ready())
        nx::fatal("Castlevania PS4: fullscreen mode requires VideoOut");
    cpu.x[0] = kFullscreenMode;
}
void nx_castlevania_fullscreen(nx::CPU& cpu, void (*)(nx::CPU&)) {
    cpu.x[0] = kazuma::ps4::video::ready() ? 1 : 0;
}
