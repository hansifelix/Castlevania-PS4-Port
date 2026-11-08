// Kazuma Traducoes PS4: portable version of Castlevania's loading animation
// hook, adapted from SwonDev/cstlvnia-blmont-to-macos
// games/castlevania/loading_animation.cpp @ 4043f21bb4f656d34cd17ba070238c7728d00631 (MIT).
// No host graphics stubs: preserve actual guest call order and material writes.
#include <nx/runtime.h>
#include <atomic>
#include <cstdint>

void nx_castlevania_loading_material(nx::CPU& c, void (*original)(nx::CPU&)) {
    // Fail loudly if the AOT wrapper's required original target is absent.
    if (!original)
        nx::fatal("Castlevania PS4: loading material original function absent");

    const uint64_t self = c.x[0];
    const uint64_t settings = self ? nx::ld<uint64_t>(self + 0x38) : 0;
    const uint64_t material = settings ? nx::ld<uint64_t>(settings + 0x18) : 0;
    if (material) {
        nx::CPU frame = c;
        frame.x[0] = self;
        frame.x[1] = 0;
        nx::call(frame, NX_BASE + 0x1dcc470); // GetCurrentAnimationFrameIndex
        nx::CPU prepare = c;
        prepare.x[0] = material;
        prepare.x[1] = nx::ld<uint32_t>(self + 0x48);
        prepare.x[2] = 0;
        prepare.v[0].f32[0] = frame.v[0].f32[0];
        nx::call(prepare, NX_BASE + 0x4e1aba0);
        static std::atomic<unsigned> logged{0};
        if (logged.fetch_add(1) < 8)
            nx::log("loading: initialized material before assignment, frame %g",
                    frame.v[0].f32[0]);
    }
    original(c);
}
