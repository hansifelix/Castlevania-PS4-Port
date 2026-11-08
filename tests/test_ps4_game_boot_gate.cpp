#include "castlevania_resolution.hpp"
#include <nx/game.h>
#include <nx/cpu.h>
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdint>
#include <stdexcept>
#include <string>

namespace {
uint32_t detected_width = 0, detected_height = 0;
unsigned videoout_queries = 0;
}
namespace nx::plat {
void screen_size(uint32_t& width, uint32_t& height) {
    ++videoout_queries;
    width = detected_width;
    height = detected_height;
}
}
namespace nx {
[[noreturn]] void fatal(const char* fmt, ...) {
    char buffer[256];
    va_list args; va_start(args, fmt);
    std::vsnprintf(buffer, sizeof(buffer), fmt, args);
    va_end(args);
    throw std::runtime_error(buffer);
}
[[noreturn]] void unimpl(CPU&, uint64_t, const char* msg) {
    throw std::runtime_error(msg);
}
}
int main() {
    using kazuma::ps4::video::ready;
    using kazuma::ps4::video::native_size;
    using kazuma::ps4::video::render_size;
    assert(std::string(nx::game::kInfo.id) == "castlevania");
    assert(nx::game::kInfo.program_id == 0x0100BA4026E94000ull);
    assert(nx::game::kInfo.strict_imports);

    // A missing VideoOut MUST prevent entry into the recompiled nnMain.
    bool rejected = false;
    assert(!ready());
    try { nx::game::after_init(); }
    catch (const std::runtime_error& e) {
        rejected = std::string(e.what()).find("VideoOut") != std::string::npos;
    }
    assert(rejected && !ready() && videoout_queries == 1);

    detected_width = 1920; detected_height = 1079; rejected = false;
    try { nx::game::after_init(); }
    catch (const std::runtime_error&) { rejected = true; }
    assert(rejected && !ready() && videoout_queries == 2);

    // Real resolution returned by the display provider gets registered.
    detected_width = 1920; detected_height = 1080;
    nx::game::after_init();
    assert(ready() && videoout_queries == 3);
    uint32_t w = 0, h = 0;
    native_size(w, h);
    assert(w == 1920 && h == 1080);
    assert(kazuma::ps4::video::select_render(1280, 720));
    render_size(w, h);
    assert(w == 1280 && h == 720);

    // Changing the effective display resolution resets render size correctly.
    detected_width = 1280; detected_height = 720;
    nx::game::after_init();
    native_size(w, h);
    assert(w == 1280 && h == 720);
    render_size(w, h);
    assert(w == 1280 && h == 720);
    assert(videoout_queries == 4);
    nx::game::renderer_start();
    nx::game::first_frame();
}
