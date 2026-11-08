#include "castlevania_resolution.hpp"
#include <nx/cpu.h>
#include <cassert>
#include <stdexcept>
#include <string>
namespace nx {
[[noreturn]] void unimpl(CPU&, uint64_t, const char* msg) {
    throw std::runtime_error(msg);
}
}
void nx_castlevania_render_resolution(nx::CPU&);
void nx_castlevania_framebuffer_resolution(nx::CPU&);
void nx_castlevania_depth_resolution(nx::CPU&);
int main() {
    using namespace kazuma::ps4::video;
    nx::CPU c{};
    assert(!ready());
    bool denied = false;
    try { nx_castlevania_framebuffer_resolution(c); }
    catch (const std::runtime_error& e) {
        denied = std::string(e.what()).find("VideoOut") != std::string::npos;
    }
    assert(denied);
    assert(!configure_native(0, 0));
    assert(!configure_native(1920, 1079));
    assert(!select_render(1280, 720));
    assert(configure_native(1920, 1080));
    assert(ready());
    uint32_t w = 0, h = 0;
    native_size(w, h); assert(w == 1920 && h == 1080);
    assert(select_render(1280, 720));
    assert(!select_render(2560, 1440));
    assert(!select_render(800, 480));
    c = {}; c.x[1] = 1920; c.x[2] = 1080;
    nx_castlevania_render_resolution(c);
    assert(c.x[1] == 1280 && c.x[2] == 720);
    c.x[1] = 800; c.x[2] = 600;
    nx_castlevania_render_resolution(c);
    assert(c.x[1] == 800 && c.x[2] == 600);
    c = {}; nx_castlevania_framebuffer_resolution(c);
    assert(c.x[0] == 1920 && c.x[1] == 1080);
    c = {}; nx_castlevania_depth_resolution(c);
    assert(c.x[1] == 1920 && c.x[2] == 1080);
    assert(configure_native(1280, 720));
    assert(!select_render(1920, 1080));
    c = {}; nx_castlevania_framebuffer_resolution(c);
    assert(c.x[0] == 1280 && c.x[1] == 720);
}
