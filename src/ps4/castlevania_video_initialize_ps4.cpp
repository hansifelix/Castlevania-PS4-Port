// Kazuma Traducoes: real PS4 video-init and fullscreen-setting callbacks.
// Adapted from SwonDev MIT games/castlevania/video_options.cpp at
// 4043f21bb4f656d34cd17ba070238c7728d00631.
// PS4 has a persistent fullscreen VideoOut, not a desktop window manager.
#include <nx/runtime.h>
#include "castlevania_resolution.hpp"
#include "castlevania_video_choices.hpp"
#include <cstdint>

namespace {
constexpr uint64_t kVideoStaticUsage = NX_BASE + 0x6be3ec8ull;
constexpr uint32_t kPs4FullscreenMode = 1;
thread_local bool initializing = false;

uint64_t static_fields() {
    const uint64_t usage = nx::ld<uint64_t>(kVideoStaticUsage);
    if (!usage) return 0;
    const uint64_t klass = nx::ld<uint64_t>(usage);
    return klass ? nx::ld<uint64_t>(klass + 0xb8) : 0;
}
int selected(nx::CPU& caller, uint64_t setting) {
    if (!setting) return -1;
    const uint64_t klass = nx::ld<uint64_t>(setting);
    if (!klass) nx::fatal("Castlevania PS4: video setting class absent");
    const uint64_t method = nx::ld<uint64_t>(klass + 0x198);
    if (!method) nx::fatal("Castlevania PS4: video setting getter absent");
    nx::CPU call = caller;
    call.x[0] = setting;
    call.x[1] = nx::ld<uint64_t>(klass + 0x1a0);
    nx::call(call, method);
    return static_cast<int32_t>(call.x[0]);
}
void validate(nx::CPU& caller, uint64_t setting) {
    if (!setting) return;
    const uint64_t klass = nx::ld<uint64_t>(setting);
    if (!klass) nx::fatal("Castlevania PS4: video setting class absent");
    const uint64_t method = nx::ld<uint64_t>(klass + 0x188);
    if (!method) nx::fatal("Castlevania PS4: video setting validator absent");
    nx::CPU call = caller;
    call.x[0] = setting;
    call.x[1] = 1;
    call.x[2] = nx::ld<uint64_t>(klass + 0x190);
    nx::call(call, method);
}
struct InitGuard {
    bool old;
    InitGuard() : old(initializing) { initializing = true; }
    ~InitGuard() { initializing = old; }
};
}

void nx_castlevania_set_fullscreen_mode(nx::CPU& cpu,
                                       void (*original)(nx::CPU&)) {
    if (initializing) return; // Matches upstream anti-recursion contract.
    if (!original)
        nx::fatal("Castlevania PS4: fullscreen setter original absent");
    if (!kazuma::ps4::video::ready())
        nx::fatal("Castlevania PS4: fullscreen setter requires VideoOut");
    cpu.x[0] = kPs4FullscreenMode;
    original(cpu); // Let the game update its managed state with the real PS4 mode.
}

void nx_castlevania_video_initialize(nx::CPU& cpu,
                                    void (*original)(nx::CPU&)) {
    if (!original)
        nx::fatal("Castlevania PS4: video initialize original absent");
    if (!kazuma::ps4::video::ready())
        nx::fatal("Castlevania PS4: video initialize requires VideoOut");
    const uint64_t self = cpu.x[0];
    InitGuard guard;
    original(cpu); // Real game creates settings and lists first.
    if (!self) return;
    kazuma::ps4::video::refresh_video_choices(cpu, self);
    const uint64_t resolution = nx::ld<uint64_t>(self + 0x68);
    validate(cpu, resolution);

    // Reconcile the managed window selection with fullscreen-only PS4 output,
    // not a fabricated desktop/window switch. Retains upstream setter gating.
    const uint64_t fields = static_fields();
    const uint64_t window = nx::ld<uint64_t>(self + 0x58);
    const uint64_t modes = fields ? nx::ld<uint64_t>(fields + 0x10) : 0;
    if (!window || !modes || nx::ld<uint32_t>(modes + 24) != 4)
        return;
    const int current = selected(cpu, window);
    const int default_index = nx::ld<int32_t>(window + 0x18);
    if (current != default_index) return;
    for (uint32_t i=0;i<4;++i) {
        if (nx::ld<uint32_t>(modes + 32 + 4*i) == kPs4FullscreenMode) {
            nx::st<uint32_t>(window + 0x18, i);
            nx::st<uint32_t>(window + 0x1c, i);
            validate(cpu, window);
            return;
        }
    }
    nx::fatal("Castlevania PS4: fullscreen mode missing from game settings");
}
