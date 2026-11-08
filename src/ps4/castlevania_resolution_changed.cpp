// Kazuma Traducoes: PS4 port of Castlevania 1.1.0 resolution-change callback.
// MIT source reference: SwonDev/cstlvnia-blmont-to-macos
// games/castlevania/video_options.cpp @ 4043f21bb4f656d34cd17ba070238c7728d00631.
// Preserves original callback, setting index getter and guest screen resolution call.
// The PS4 output surface stays fixed; only the internal render extent changes.
#include <nx/runtime.h>
#include "castlevania_resolution.hpp"
#include <cstdint>

namespace {
constexpr uint64_t kStaticUsage = NX_BASE + 0x6be3ec8ull;
constexpr uint64_t kApplyResolution = NX_BASE + 0x4e00a50ull;
constexpr uint64_t kDesktopFullscreenMode = 1; // PS4 has no windowed desktop mode.

uint64_t static_fields() {
    const uint64_t usage = nx::ld<uint64_t>(kStaticUsage);
    if (!usage) return 0;
    const uint64_t klass = nx::ld<uint64_t>(usage);
    return klass ? nx::ld<uint64_t>(klass + 0xb8) : 0;
}

int selected(nx::CPU& caller, uint64_t setting) {
    if (!setting) return -1;
    const uint64_t klass = nx::ld<uint64_t>(setting);
    if (!klass)
        nx::fatal("Castlevania PS4: resolution setting has no class");
    const uint64_t method = nx::ld<uint64_t>(klass + 0x198);
    if (!method)
        nx::fatal("Castlevania PS4: resolution selection method absent");
    nx::CPU tmp = caller;
    tmp.x[0] = setting;
    tmp.x[1] = nx::ld<uint64_t>(klass + 0x1a0);
    nx::call(tmp, method);
    return static_cast<int32_t>(tmp.x[0]);
}
} // namespace

void nx_castlevania_resolution_changed(nx::CPU& cpu,
                                      void (*original)(nx::CPU&)) {
    if (!original)
        nx::fatal("Castlevania PS4: resolution change original function absent");
    const uint64_t self = cpu.x[0];
    original(cpu);
    if (!self) return;

    const uint64_t setting = nx::ld<uint64_t>(self + 0x68);
    if (!setting) return;
    const int index = selected(cpu, setting);
    const uint64_t fields = static_fields();
    if (!fields || index < 0) return;
    const uint64_t choices = nx::ld<uint64_t>(fields);
    if (!choices) return;
    const uint32_t count = nx::ld<uint32_t>(choices + 24);
    if (count == 0 || count > 32 || static_cast<uint32_t>(index) >= count)
        return; // Reject unverified layouts and invalid indexes.
    const uint64_t entry = choices + 32 + uint64_t(index) * 8;
    const uint32_t width = nx::ld<uint32_t>(entry);
    const uint32_t height = nx::ld<uint32_t>(entry + 4);
    if (!kazuma::ps4::video::select_render(width, height)) return;

    // The game's own resolution setter still runs, with the original ABI.
    nx::CPU frame = cpu;
    frame.x[0] = width;
    frame.x[1] = height;
    frame.x[2] = kDesktopFullscreenMode;
    frame.x[3] = 0x100000000ull;
    frame.x[4] = 0;
    nx::call(frame, kApplyResolution);
    // No resize_video_window: a PS4 VideoOut output is not a desktop HWND.
    nx::log("Castlevania PS4: internal render size %ux%u", width, height);
}
