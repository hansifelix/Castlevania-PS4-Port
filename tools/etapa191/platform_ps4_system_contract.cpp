// Actual PS4 service contracts not supplied by the original 8 adapters.
// Filesystem: safe recursive mkdir; display: current SceVideoOut status;
// console-only features: no touchscreen, no desktop headless mode.
// This is not a renderer or a fake game frame.
#include "platform.h"
#include <cerrno>
#include <cstdint>
#include <string>
#include <sys/stat.h>
#include <sys/types.h>

namespace nx::plat {
bool make_dirs(const std::string& path) {
    if (path.empty()) return false;
    std::string current;
    size_t i=0;
    if (path[0]=='/') current="/";
    while(i<path.size()) {
        while(i<path.size() && path[i]=='/') ++i;
        if(i==path.size()) break;
        const size_t j=path.find('/',i);
        const std::string part=path.substr(i,j==std::string::npos ? j : j-i);
        if(part=="." || part=="..") return false;
        if(!current.empty() && current.back()!='/') current+='/';
        current+=part;
        if(::mkdir(current.c_str(),0700)<0) {
            if(errno!=EEXIST) return false;
            struct stat st{};
            if(::stat(current.c_str(),&st)<0 || !S_ISDIR(st.st_mode)) return false;
        }
        if(j==std::string::npos)break;
        i=j;
    }
    return true;
}
void window_size(uint32_t& w,uint32_t& h){desktop_size(w,h);}
void screen_size(uint32_t& w,uint32_t& h){desktop_size(w,h);}
float default_render_scale(){return 1.0f;} // Full resolution, not a GPU performance promise.
size_t touch_overlay(OverlayShape*,size_t){return 0;} // Standard PS4 has no touch display.
bool headless(){return false;} // PS4 homebrew console UI is always foreground.
void start_memory_guard() {
    // A resource limit has NOT been installed; don't claim it exists.
    log_line("LINGSHU191: external memory guard unavailable on PS4");
}
uint64_t memguard_overlap_ns(uint64_t,uint64_t){return 0;} // Contract: zero where unavailable.
} // namespace nx::plat
