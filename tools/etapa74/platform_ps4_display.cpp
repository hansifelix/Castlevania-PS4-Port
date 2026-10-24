// Kazuma 74: six concrete host-display APIs used by the public nx::boot.
// PS4 has no desktop HWND. A lightweight PS4 display descriptor supplies
// dimensions; the Vulkan WSI of Kazuma 68/73 owns its VideoOut separately.
// This file DOES NOT present frames and DOES NOT create a game executable.
#include <orbis/VideoOut.h>
#include <atomic>
#include <cstdint>
#include <new>

namespace nx::plat {
namespace {
struct DisplayContext final { uint32_t width, height; };
std::atomic<uint32_t> cached_width{0};
std::atomic<uint32_t> cached_height{0};
std::atomic<uint64_t> generation{0};

bool query_display(uint32_t& w, uint32_t& h) {
    w = 0;
    h = 0;
    // Transient query: do not retain or submit through a second VideoOut
    // handle while Mesa's PS4 WSI is handling presentation.
    const int handle = sceVideoOutOpen(ORBIS_VIDEO_USER_MAIN, ORBIS_VIDEO_OUT_BUS_MAIN, 0, nullptr);
    if (handle < 0) return false;
    OrbisVideoOutResolutionStatus status{};
    const int result = sceVideoOutGetResolutionStatus(handle, &status);
    const int closed = sceVideoOutClose(handle);
    if (result < 0 || closed < 0 || status.width == 0 || status.height == 0) return false;
    w = status.width;
    h = status.height;
    return true;
}

bool ensure_dimensions() {
    if (cached_width.load(std::memory_order_acquire) &&
        cached_height.load(std::memory_order_acquire)) return true;
    uint32_t w = 0, h = 0;
    if (!query_display(w, h)) return false;
    cached_width.store(w, std::memory_order_release);
    cached_height.store(h, std::memory_order_release);
    return true;
}
} // namespace

void* create_window() {
    uint32_t w = 0, h = 0;
    if (!query_display(w, h)) return nullptr; // explicit failure, not a fake window
    auto* d = new (std::nothrow) DisplayContext{w,h};
    if (!d) return nullptr;
    cached_width.store(w, std::memory_order_release);
    cached_height.store(h, std::memory_order_release);
    generation.fetch_add(1, std::memory_order_acq_rel);
    return static_cast<void*>(d);
}

void release_window(void* handle) {
    if (!handle) return;
    delete static_cast<DisplayContext*>(handle);
    cached_width.store(0, std::memory_order_release);
    cached_height.store(0, std::memory_order_release);
    generation.fetch_add(1, std::memory_order_acq_rel);
}

uint64_t window_generation() { return generation.load(std::memory_order_acquire); }

bool window_minimized() {
    // On PS4, the display isn't a conventional minimized desktop window.
    // A missing display is treated as unavailable; suspend is not handled yet.
    return !ensure_dimensions();
}

void window_size(uint32_t& w, uint32_t& h) {
    if (!ensure_dimensions()) { w = 0; h = 0; return; }
    w = cached_width.load(std::memory_order_acquire);
    h = cached_height.load(std::memory_order_acquire);
}

void screen_size(uint32_t& w, uint32_t& h) { window_size(w, h); }
} // namespace nx::plat
