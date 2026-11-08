#pragma once
// Synthetic subset for host tests. Production uses upstream's real nx/game.h.
#include <cstdint>
namespace nx::game {
struct Info {
    const char* id; const char* title; uint64_t program_id;
    const char* android_package; const char* pc_data_root;
    uint64_t system_resource_size = 0;
    bool strict_imports = false, switch2bridge = false;
    bool native_render_resolution = false, deferred_bindings = false;
};
extern const Info kInfo;
void after_init();
void renderer_start();
void first_frame();
}
