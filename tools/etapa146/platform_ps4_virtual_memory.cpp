// LINGSHU LAB 146 — fail-closed provisional PS4 virtual-memory adapter.
// The host uses fixed guest addresses. Never overwrite pre-existing mappings.
// IMPORTANT: compilation is NOT hardware validation. Large fixed guest ranges
// may be unavailable on actual PS4 and must be checked before boot attempts.
#include "platform.h"
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <mutex>
#include <utility>
#include <vector>
#include <sys/mman.h>
#include <unistd.h>

namespace nx::plat {
namespace {
struct Range { uint64_t first, end; };
std::mutex ranges_lock;
std::vector<Range> reservations;

uint64_t page_bytes() {
    long size=sysconf(_SC_PAGESIZE);
    if (size<=0) return 0;
    uint64_t n=static_cast<uint64_t>(size);
    return (n & (n-1)) ? 0 : n;
}

bool round_range(uint64_t addr,uint64_t size,uint64_t page,
                 uint64_t& lo,uint64_t& hi) {
    if (!page || size==0 || addr>std::numeric_limits<uint64_t>::max()-size)
        return false;
    const uint64_t end=addr+size;
    const uint64_t mask=page-1;
    if (end>std::numeric_limits<uint64_t>::max()-mask) return false;
    lo=addr & ~mask;
    hi=(end+mask) & ~mask;
    return hi>lo && (hi-lo)<=static_cast<uint64_t>(SIZE_MAX);
}
bool covered(uint64_t lo,uint64_t hi) {
    for (const auto& range:reservations) {
        if (range.first<=lo && hi<=range.end) return true;
    }
    return false;
}
}

// Reserve *without* MAP_FIXED. MAP_FIXED could silently evict unrelated
// host allocations and corrupt the console process. A hint is not a promise:
// if OS selects any other address, discard its mapping and fail the call.
bool reserve(uint64_t addr,uint64_t size) {
    const uint64_t page=page_bytes();
    if (!page || addr%page || size%page || !size ||
        addr>std::numeric_limits<uint64_t>::max()-size) return false;
    if (addr>static_cast<uint64_t>(UINTPTR_MAX)) return false;
    std::lock_guard<std::mutex> lock(ranges_lock);
    for (const auto& r:reservations)
        if (addr<r.end && r.first<addr+size) return false;
    void* result=mmap(reinterpret_cast<void*>(static_cast<uintptr_t>(addr)),
                      static_cast<size_t>(size), PROT_NONE,
                      MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if (result==MAP_FAILED) return false;
    if (reinterpret_cast<uintptr_t>(result)!=addr) {
        munmap(result,static_cast<size_t>(size));
        return false;
    }
    reservations.push_back({addr,addr+size});
    return true;
}

bool commit(uint64_t addr,uint64_t size) {
    uint64_t lo=0,hi=0;
    if (!round_range(addr,size,page_bytes(),lo,hi)) return false;
    std::lock_guard<std::mutex> lock(ranges_lock);
    if (!covered(lo,hi)) return false;
    return mprotect(reinterpret_cast<void*>(static_cast<uintptr_t>(lo)),
                    static_cast<size_t>(hi-lo),PROT_READ|PROT_WRITE)==0;
}

void decommit(uint64_t addr,uint64_t size) {
    uint64_t lo=0,hi=0;
    const uint64_t page=page_bytes();
    if (!round_range(addr,size,page,lo,hi)) return;
    std::lock_guard<std::mutex> lock(ranges_lock);
    if (!covered(lo,hi)) return;

    // Partial head/tail pages cannot be protected without destroying bytes
    // belonging to adjacent live allocations; clear just the requested bytes.
    const uint64_t end=addr+size;
    const uint64_t inner_begin=(addr+page-1)&~(page-1);
    const uint64_t inner_end=end & ~(page-1);
    if (inner_begin>=inner_end) {
        std::memset(reinterpret_cast<void*>(static_cast<uintptr_t>(addr)),0,
                    static_cast<size_t>(size));
        return;
    }
    if (addr<inner_begin)
        std::memset(reinterpret_cast<void*>(static_cast<uintptr_t>(addr)),0,
                    static_cast<size_t>(inner_begin-addr));
    if (inner_end<end)
        std::memset(reinterpret_cast<void*>(static_cast<uintptr_t>(inner_end)),0,
                    static_cast<size_t>(end-inner_end));
    void* p=reinterpret_cast<void*>(static_cast<uintptr_t>(inner_begin));
    size_t n=static_cast<size_t>(inner_end-inner_begin);
    // Zero data as a fallback if MADV_DONTNEED is unavailable or rejected.
    // These pages must still be writable at the time of decommit.
#if defined(MADV_DONTNEED)
    if (madvise(p,n,MADV_DONTNEED)!=0) std::memset(p,0,n);
#else
    std::memset(p,0,n);
#endif
    mprotect(p,n,PROT_NONE);
}
} // namespace nx::plat
