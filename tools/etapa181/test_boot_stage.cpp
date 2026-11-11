// Stage 181: exercise PRODUCTION boot entry and PRODUCTION POSIX log file.
// nx::boot() is stubbed ONLY in this host unit test; it is not an ELF/PKG.
// Never includes, loads, or distributes any game material.
#include "platform.h"
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>

#define main lingshu181_real_entry_under_test
#include "../etapa162/ps4_boot_link_entry.cpp"
#undef main

namespace {
bool allow_layout=false, allow_image=false;
int layout_calls=0,image_calls=0,boot_calls=0;
}
extern "C" bool lingshu_ps4_guest_layout_valid() {
    ++layout_calls;return allow_layout;
}
extern "C" bool lingshu_ps4_boot_images_present() {
    ++image_calls;return allow_image;
}
namespace nx { void boot() {++boot_calls;} }
#define CHECK(expr) do {if(!(expr)){std::fprintf(stderr, "LINGSHU181_FAIL line=%d expr=%s\\n",__LINE__,#expr);return 1;}}while(0)

int main() {
    using nx::plat::data_root;
    const std::string path=data_root()+"/boot.log";
    CHECK(!path.empty());
    // This test must be executed with KAZUMA_DATA_ROOT in an empty temp dir.
    const int a=lingshu181_real_entry_under_test();
    CHECK(a==3 && layout_calls==1 && image_calls==0 && boot_calls==0);
    allow_layout=true;
    const int b=lingshu181_real_entry_under_test();
    CHECK(b==2 && layout_calls==2 && image_calls==1 && boot_calls==0);
    allow_image=true;
    const int c=lingshu181_real_entry_under_test();
    CHECK(c==0 && layout_calls==3 && image_calls==2 && boot_calls==1);
    std::ifstream in(path);
    CHECK(bool(in));
    std::vector<std::string> messages;
    for(std::string line;std::getline(in,line);) messages.push_back(line);
    const std::vector<std::string> expected{
        "LINGSHU181_BOOT_ENTRY_STARTED",
        "LINGSHU181_BOOT_REJECTED_GUEST_LAYOUT",
        "LINGSHU181_BOOT_ENTRY_STARTED",
        "LINGSHU181_GUEST_LAYOUT_CHECKED_NOT_HARDWARE_MAPPED",
        "LINGSHU181_BOOT_REJECTED_AOT_IMAGE",
        "LINGSHU181_BOOT_ENTRY_STARTED",
        "LINGSHU181_GUEST_LAYOUT_CHECKED_NOT_HARDWARE_MAPPED",
        "LINGSHU181_AOT_IMAGE_VERIFIED_CALLING_REAL_NX_BOOT",
        "LINGSHU181_NX_BOOT_RETURNED_NO_FRAME_ASSERTION",
    };
    CHECK(messages==expected);
    std::puts("LINGSHU181_REAL_BOOT_STAGE_LOG=PASSED_3_BRANCHES_9_PERSISTENT_MARKERS_NO_GAME");
}
