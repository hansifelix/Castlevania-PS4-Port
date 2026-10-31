// Etapa 178: synthetic metadata tests using the pinned ORIGINAL nx headers.
// No game data, no PS4 hardware mapping, no fake success frames.
#include <nx/runtime.h>
#include <array>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <span>
#include "platform.h"

namespace {
nx::ModuleInfo a{}, b{}, c{}; // Explicit zero initialization: keep all upstream fields valid.
struct SyntheticModules {
    SyntheticModules() {
        a.name="main"; a.base=nx::kModuleBase; a.bss=0x10000; a.bss_size=0x4000;
        b.name="sdk"; b.base=nx::kModuleBase+0x10000000; b.bss=0x20000; b.bss_size=0x4000;
        c.name="subsdk0"; c.base=nx::kModuleBase+0x20000000; c.bss=0x30000; c.bss_size=0x4000;
    }
} synthetic_modules;
size_t count=3;
std::string diagnostic;
} // namespace
namespace nx {
std::span<const ModuleInfo* const> linked_modules() {
    static const ModuleInfo* const mods[]={&a,&b,&c};
    return {mods,count};
}
} // namespace
namespace nx::plat {
void log_line(const char* line) { diagnostic = line ? line : ""; }
}
extern "C" bool lingshu_ps4_guest_layout_valid();

#define CHECK(condition) do { if (!(condition)) { \
    std::fprintf(stderr, "LINGSHU178_FAILED line %d: %s; last=%s\n", \
                 __LINE__, #condition, diagnostic.c_str()); return 1; } } while (0)

int main() {
    int cases=0;
    auto accept=[&]() { CHECK(lingshu_ps4_guest_layout_valid()); ++cases; return 0; };
    auto reject=[&](const char* message) {
        CHECK(!lingshu_ps4_guest_layout_valid());
        CHECK(diagnostic.find(message)!=std::string::npos);
        ++cases;
        return 0;
    };
    CHECK(accept()==0);
    count=2;
    CHECK(reject("three AOT modules")==0);
    count=3;

    const char* orig_name=b.name;
    b.name="wrong";
    CHECK(reject("unexpected AOT")==0);
    b.name=orig_name;

    const uint64_t orig_base=b.base, orig_bss=b.bss;
    b.base=0;
    CHECK(reject("overflow / outside")==0);
    b.base=orig_base;

    b.base=a.base;
    CHECK(reject("overlap")==0);
    b.base=orig_base;

    b.bss=UINT64_MAX;
    CHECK(reject("overflow")==0);
    b.bss=orig_bss;

    c.base=nx::kAddressSpaceBase+nx::kAddressSpaceSize-0x4000;
    c.bss=0x8000;
    CHECK(reject("beyond guest")==0);
    c.base=nx::kModuleBase+0x20000000;
    c.bss=0x30000;

    c.base=nx::kHeapBase-0x1000;
    c.bss=0x10000;
    CHECK(reject("regions overlap")==0);
    c.base=nx::kModuleBase+0x20000000;
    c.bss=0x30000;

    b.base=nx::kModuleBase-0x4000;
    CHECK(reject("overflow / outside")==0);
    b.base=orig_base;

    c.bss_size=UINT64_MAX;
    CHECK(reject("overflow")==0);
    c.bss_size=0x4000;

    CHECK(accept()==0);
    CHECK(cases==11);
    std::printf("LINGSHU178_GUEST_LAYOUT_HOST=PASSED_%d_CASES_NO_GAME\n",cases);
    return 0;
}
