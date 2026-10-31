// LINGSHU182: execute real pinned upstream nx::memory_init + production
// PS4 virtual memory adapter on Linux. All AOT metadata below is synthetic.
// Exercises the actual fixed guest address layout at native Linux addresses,
// NOT on PS4. No code from commercial game or renderer.
#include <nx/runtime.h>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <span>
#include <string>
#include "platform.h"

namespace {
nx::ModuleInfo main_module{};
nx::ModuleInfo sdk_module{};
nx::ModuleInfo subsdk_module{};
struct SetUp {
    SetUp() {
        main_module.name="main";
        main_module.base=nx::kModuleBase;
        main_module.bss=0x02000000;
        main_module.bss_size=0x4000;
        sdk_module.name="sdk";
        sdk_module.base=nx::kModuleBase+0x10000000;
        sdk_module.bss=0x01000000;
        sdk_module.bss_size=0x4000;
        subsdk_module.name="subsdk0";
        subsdk_module.base=nx::kModuleBase+0x20000000;
        subsdk_module.bss=0x01000000;
        subsdk_module.bss_size=0x4000;
    }
} setup;
}
namespace nx {
std::span<const ModuleInfo* const> linked_modules() {
    static const ModuleInfo* const modules[]{
        &main_module,&sdk_module,&subsdk_module
    };
    return modules;
}
void log(const char* format, ...) {
    std::va_list args;
    va_start(args,format);
    std::vfprintf(stderr,format,args);
    std::fputc('\n',stderr);
    va_end(args);
}
[[noreturn]] void fatal(const char* format, ...) {
    std::va_list args;
    va_start(args,format);
    std::vfprintf(stderr,format,args);
    std::fputc('\n',stderr);
    va_end(args);
    std::abort();
}
}
#define CHECK(expr) do {if(!(expr)){std::fprintf(stderr,"LINGSHU182_FAILED line %d: %s\n",__LINE__,#expr);return 1;}}while(0)
int main() {
    int cases=0;
    // This is the true runtime memory_init, reserving all of the actual
    // guest virtual address ranges, not a reimplementation of its math.
    nx::memory_init();
    ++cases;
    CHECK(nx::vm_query(nx::kAliasBase+0x2000).state==nx::kMemFree);
    ++cases;
    CHECK(nx::vm_query(nx::kStackBase+0x2000).state==nx::kMemFree);
    ++cases;
    CHECK(nx::vm_query(nx::kHeapBase).state==nx::kMemInaccessible);
    ++cases;
    CHECK(nx::vm_query(nx::kKernelBase+0x2000).state==nx::kMemInaccessible);
    ++cases;
    const uint64_t addr=nx::kernel_alloc(0x3000);
    CHECK(addr>=nx::kKernelBase && addr<nx::kKernelBase+nx::kKernelSize);
    ++cases;
    auto* kernel_byte=reinterpret_cast<unsigned char*>(static_cast<uintptr_t>(addr));
    kernel_byte[0]=0x5a;
    kernel_byte[0x2000]=0x6b;
    CHECK(kernel_byte[0]==0x5a && kernel_byte[0x2000]==0x6b);
    ++cases;
    // Exercise actual upstream commit/decommit delegating to production adapter.
    CHECK(nx::commit(nx::kHeapBase,0x4000));
    ++cases;
    auto* heap=reinterpret_cast<unsigned char*>(static_cast<uintptr_t>(nx::kHeapBase));
    std::memset(heap,0x7c,0x4000);
    nx::decommit(nx::kHeapBase,0x4000);
    nx::decommit(nx::kHeapBase,0x4000);  // former PROT_NONE crash
    ++cases;
    CHECK(nx::commit(nx::kHeapBase,0x4000));
    ++cases;
    CHECK(heap[0]==0 && heap[0x3fff]==0);
    ++cases;
    CHECK(!nx::commit(nx::kAddressSpaceBase-0x4000,0x4000));
    ++cases;
    std::printf("LINGSHU182_REAL_UPSTREAM_MEMORY_INIT=PASSED_%d_CASES_HOST_ONLY_NO_GAME\n",cases);
    return 0;
}
