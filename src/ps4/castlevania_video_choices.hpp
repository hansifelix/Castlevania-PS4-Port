#pragma once
#include <cstdint>
namespace nx { struct CPU; }
namespace kazuma::ps4::video {
// Refresh the verified managed video-choice arrays after the game's original
// initialization. Uses the actual PS4 VideoOut resolution provider.
void refresh_video_choices(nx::CPU& cpu, uint64_t self);
}
