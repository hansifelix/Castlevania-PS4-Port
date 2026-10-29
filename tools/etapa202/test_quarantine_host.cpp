// Lingshu202 — the REAL stage146 VM adapter, fake mmap/munmap on Linux.
// No real virtual-memory manipulation, game image, or PS4 execution.
#include <cassert>
#include <cerrno>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <sys/mman.h>
#include "platform.h"

namespace {
std::string logs;
enum class Mode { MmapError, Exact, Relocated };
Mode mode=Mode::MmapError;
bool fail_cleanup=false;
unsigned maps=0, unmaps=0, protects=0, advises=0;
}
namespace nx {
void log(const char* fmt,...) {
    char buf[1024];
    va_list args;
    va_start(args,fmt);
    std::vsnprintf(buf,sizeof(buf),fmt,args);
    va_end(args);
    logs += buf;
    logs.push_back('\n');
}
}
extern "C" void* __wrap_mmap(void* hint, size_t size, int protection,
                            int flags, int fd, off_t offset) {
    (void)fd;(void)offset;
    assert(size == 0x4000);
    assert(protection == PROT_NONE);
    assert((flags & MAP_PRIVATE) != 0);
    ++maps;
    if (mode==Mode::MmapError) {errno=EINVAL;return MAP_FAILED;}
    auto addr=reinterpret_cast<std::uintptr_t>(hint);
    if (mode==Mode::Relocated) addr+=0x4000;
    return reinterpret_cast<void*>(addr);
}
extern "C" int __wrap_munmap(void* actual,size_t size) {
    ++unmaps;
    assert(actual && size==0x4000);
    if (fail_cleanup) {errno=EIO;return -1;}
    return 0;
}
extern "C" int __wrap_mprotect(void*,size_t,int) {
    ++protects;
    return 0;
}
extern "C" int __wrap_madvise(void*,size_t,int) {
    ++advises;
    return 0;
}
int main() {
    constexpr std::uint64_t page=0x4000;
    constexpr std::uint64_t address=0x100000000;
    assert(!nx::plat::reserve(address+1,page));
    assert(maps==0);

    mode=Mode::MmapError;
    assert(!nx::plat::reserve(address,page));
    assert(maps==1 && unmaps==0);
    assert(logs.find("LINGSHU184_VM=MMAP_FAILED")!=std::string::npos);

    mode=Mode::Relocated;
    assert(!nx::plat::reserve(address,page));
    assert(maps==2 && unmaps==1);
    // A successfully cleaned relocation is not a permanent failure.
    mode=Mode::Exact;
    assert(nx::plat::reserve(address,page));
    assert(maps==3 && unmaps==1);

    // Another relocation fails to clean up: do not let any memory API proceed.
    mode=Mode::Relocated;
    fail_cleanup=true;
    assert(!nx::plat::reserve(address+0x10000,page));
    assert(maps==4 && unmaps==2);
    assert(logs.find("LINGSHU202_VM=RELOCATED_CLEANUP_FAILED_QUARANTINE")!=std::string::npos);

    mode=Mode::Exact;
    assert(!nx::plat::reserve(address+0x20000,page));
    assert(maps==4); // no new kernel mappings after an unknown mapping
    assert(!nx::plat::commit(address,page));
    nx::plat::decommit(address,page);
    assert(protects==0 && advises==0);
    assert(logs.find("LINGSHU202_VM=QUARANTINED_RESERVE_STOP")!=std::string::npos);
    assert(logs.find("LINGSHU202_VM=QUARANTINED_COMMIT_STOP")!=std::string::npos);
    assert(logs.find("LINGSHU202_VM=QUARANTINED_DECOMMIT_STOP")!=std::string::npos);
    std::puts("LINGSHU202_QUARANTINE=PASS_LINUX_SIMULATED_SYSCALLS_NOT_PS4");
}
