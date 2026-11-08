#pragma once
#include <cstdint>

// Integration contract: the actual PS4 VideoOut backend MUST provide the
// native framebuffer size before these hooks can run. No guessed 1080p.
namespace kazuma::ps4::video {
bool configure_native(uint32_t width, uint32_t height) noexcept;
bool select_render(uint32_t width, uint32_t height) noexcept;
bool ready() noexcept;
void native_size(uint32_t& width, uint32_t& height) noexcept;
void render_size(uint32_t& width, uint32_t& height) noexcept;
}
