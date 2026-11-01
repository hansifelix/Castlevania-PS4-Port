// PS4-style 16 KiB *logical* pages, using real Linux mmap/mprotect/madvise.
// Only sysconf(_SC_PAGESIZE) is overridden. NOT a PS4 hardware test.
#include "platform.h"
#include <sys/mman.h>
#include <unistd.h>
#include <cstdint>
#include <cstdio>
#include <cstring>

extern "C" long __real_sysconf(int name);
extern "C" long __wrap_sysconf(int name) {
    if (name==_SC_PAGESIZE) return 16384;
    return __real_sysconf(name);
}
#define CHECK(x) do { if (!(x)) { \
  std::fprintf(stderr,"LINGSHU16K_FAIL %s at line %d\\n",#x,__LINE__); \
  return 1; } } while (0)

int main() {
    constexpr size_t page=16384;
    constexpr size_t bytes=page*4;
    // Linux might map only at 4 KiB boundaries; request spare room
    // and choose a suitable 16 KiB-aligned hint without MAP_FIXED.
    void* suggestion=mmap(nullptr,bytes+page,PROT_NONE,
                          MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    CHECK(suggestion!=MAP_FAILED);
    const uintptr_t origin=reinterpret_cast<uintptr_t>(suggestion);
    const uintptr_t aligned=(origin+page-1)&~(uintptr_t(page-1));
    CHECK(munmap(suggestion,bytes+page)==0);
    const uint64_t base=static_cast<uint64_t>(aligned);
    CHECK(nx::plat::reserve(base,bytes));
    CHECK(nx::plat::commit(base,bytes));
    auto* p=reinterpret_cast<unsigned char*>(aligned);
    std::memset(p,0x5a,bytes);

    // Clear across two *logical* 16 KiB page boundaries without
    // accidentally discarding untouched neighbors.
    nx::plat::decommit(base+page-7,20);
    CHECK(p[page-8]==0x5a);
    for (size_t n=page-7;n<page+13;++n) CHECK(p[n]==0);
    CHECK(p[page+13]==0x5a);
    CHECK(p[0]==0x5a && p[2*page]==0x5a);

    // Fully decommit one 16 KiB logical page and recommit it.
    nx::plat::decommit(base+2*page,page);
    CHECK(nx::plat::commit(base+2*page,page));
    for (size_t n=2*page;n<3*page;++n) CHECK(p[n]==0);
    CHECK(p[page+13]==0x5a && p[3*page]==0x5a);

    // Unaligned commit rounds to the simulated logical page boundary.
    nx::plat::decommit(base+3*page,page);
    CHECK(nx::plat::commit(base+3*page+17,3));
    CHECK(p[3*page]==0 && p[bytes-1]==0);
    CHECK(munmap(reinterpret_cast<void*>(aligned),bytes)==0);
    std::puts("LINGSHU179_LOGICAL_16K_PAGES=PASSED_HOST_ONLY");
    return 0;
}
