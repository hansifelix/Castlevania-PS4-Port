// Test hardware-facing contract with an explicit mock on the host, NEVER as PS4 proof.
#include <orbis/VideoOut.h>
#include <cassert>
#include <cstdint>
#include <cstdio>

static int opens=0, closes=0, probes=0;
static bool fail_open=false, fail_status=false;
static uint32_t width=1920, height=1080;
extern "C" {
int32_t sceVideoOutOpen(int32_t user, int32_t bus, int32_t idx, const void* param) {
    assert(user==ORBIS_VIDEO_USER_MAIN && bus==ORBIS_VIDEO_OUT_BUS_MAIN);
    assert(idx==0 && param==nullptr);
    opens++;
    return fail_open?-1:34;
}
int32_t sceVideoOutGetResolutionStatus(int32_t handle, OrbisVideoOutResolutionStatus* out) {
    assert(handle==34 && out!=nullptr);
    probes++;
    if (fail_status) return -2;
    out->width=width; out->height=height;
    return 0;
}
int32_t sceVideoOutClose(int32_t handle) { assert(handle==34); closes++; return 0; }
}
namespace nx::plat {
void* create_window();
void release_window(void*);
uint64_t window_generation();
bool window_minimized();
void window_size(uint32_t&, uint32_t&);
void screen_size(uint32_t&, uint32_t&);
}
int main() {
    using namespace nx::plat;
    uint32_t w=111,h=222;
    assert(window_generation()==0);
    screen_size(w,h);
    assert(w==1920 && h==1080);
    const int first_open=opens;
    window_size(w,h);
    assert(opens==first_open); // cached, no per-frame VideoOut open
    void* display=create_window();
    assert(display!=nullptr && window_generation()==1 && !window_minimized());
    assert(opens==closes);
    release_window(display);
    assert(window_generation()==2);
    width=1280; height=720;
    display=create_window();
    assert(display);
    window_size(w,h);
    assert(w==1280 && h==720);
    release_window(display);
    // When query fails, never fabricate a 1920x1080 answer.
    fail_open=true;
    w=111; h=222;
    assert(create_window()==nullptr);
    window_size(w,h);
    assert(w==0 && h==0 && window_minimized());
    fail_open=false;
    fail_status=true;
    assert(create_window()==nullptr);
    window_size(w,h);
    assert(w==0 && h==0);
    fail_status=false;
    assert(opens>=probes && probes>=closes && closes>=2);
    puts("KAZUMA74 HOST: contrato de display verificável, sem quadro falso = OK");
}
