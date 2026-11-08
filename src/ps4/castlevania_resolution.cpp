#include "castlevania_resolution.hpp"
#include <atomic>
#include <cstdint>
#include <nx/cpu.h>

namespace {
std::atomic<uint64_t> native_dimensions{0};
std::atomic<uint64_t> render_dimensions{0};
constexpr uint64_t pack(uint32_t w, uint32_t h) noexcept {
    return (uint64_t(w) << 32) | h;
}
void unpack(uint64_t packed, uint32_t& w, uint32_t& h) noexcept {
    w = static_cast<uint32_t>(packed >> 32);
    h = static_cast<uint32_t>(packed);
}
bool valid_16x9(uint32_t w, uint32_t h) noexcept {
    return w >= 640 && h >= 360 && w <= 3840 && h <= 2160 &&
           uint64_t(w) * 9u == uint64_t(h) * 16u;
}
uint64_t require_ready(nx::CPU& cpu) {
    const uint64_t dimensions = native_dimensions.load(std::memory_order_acquire);
    if (!dimensions)
        nx::unimpl(cpu, 0, "Castlevania PS4: VideoOut size not configured");
    return dimensions;
}
}

namespace kazuma::ps4::video {
bool configure_native(uint32_t width, uint32_t height) noexcept {
    if (!valid_16x9(width, height)) return false;
    render_dimensions.store(pack(width, height), std::memory_order_release);
    native_dimensions.store(pack(width, height), std::memory_order_release);
    return true;
}
bool select_render(uint32_t width, uint32_t height) noexcept {
    if (!valid_16x9(width, height)) return false;
    uint32_t nw = 0, nh = 0;
    unpack(native_dimensions.load(std::memory_order_acquire), nw, nh);
    if (!nw || width > nw || height > nh) return false;
    render_dimensions.store(pack(width, height), std::memory_order_release);
    return true;
}
bool ready() noexcept {
    return native_dimensions.load(std::memory_order_acquire) != 0;
}
void native_size(uint32_t& width, uint32_t& height) noexcept {
    unpack(native_dimensions.load(std::memory_order_acquire), width, height);
}
void render_size(uint32_t& width, uint32_t& height) noexcept {
    unpack(render_dimensions.load(std::memory_order_acquire), width, height);
}
}

// These exact C++ signatures match the three upstream AOT callbacks.
// Framebuffer: x0=width, x1=height. Depth: x1=width, x2=height.
// Render hook rewrites only the two known legacy render-size requests.
void nx_castlevania_render_resolution(nx::CPU& cpu) {
    (void)require_ready(cpu);
    if ((cpu.x[1] == 1920 && cpu.x[2] == 1080) ||
        (cpu.x[1] == 1280 && cpu.x[2] == 720)) {
        uint32_t w, h;
        kazuma::ps4::video::render_size(w, h);
        cpu.x[1] = w;
        cpu.x[2] = h;
    }
}
void nx_castlevania_framebuffer_resolution(nx::CPU& cpu) {
    uint32_t w, h;
    unpack(require_ready(cpu), w, h);
    cpu.x[0] = w;
    cpu.x[1] = h;
}
void nx_castlevania_depth_resolution(nx::CPU& cpu) {
    uint32_t w, h;
    unpack(require_ready(cpu), w, h);
    cpu.x[1] = w;
    cpu.x[2] = h;
}
