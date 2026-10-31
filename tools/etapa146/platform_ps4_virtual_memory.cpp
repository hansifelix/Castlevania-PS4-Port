// LINGSHU LAB 179 — fail-closed PS4 virtual-memory adapter.
// Tested with Linux POSIX syscalls. Actual PS4 memory mapping UNVERIFIED.
#include "platform.h"
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <mutex>
#include <map>
#include <vector>
#include <sys/mman.h>
#include <unistd.h>

namespace nx::plat {
namespace {
struct Range { uint64_t first, end; };
std::mutex ranges_lock;
std::vector<Range> reservations;
// Track pages that are really writable after a successful mprotect.
std::map<uint64_t,uint64_t> writable;
void mark_writable(uint64_t lo,uint64_t hi) {
    auto it=writable.lower_bound(lo);
    if (it!=writable.begin()) {
        auto prev=std::prev(it);
        if (prev->second>=lo) {
            lo=prev->first;
            if (prev->second>hi) hi=prev->second;
            it=writable.erase(prev);
        }
    }
    while (it!=writable.end() && it->first<=hi) {
        if (it->second>hi) hi=it->second;
        it=writable.erase(it);
    }
    writable.emplace(lo,hi);
}
void unmark_writable(uint64_t lo,uint64_t hi) {
    auto it=writable.lower_bound(lo);
    if (it!=writable.begin()) {
        auto prev=std::prev(it);
        if (prev->second>lo) it=prev;
    }
    while (it!=writable.end() && it->first<hi) {
        const uint64_t a=it->first,b=it->second;
        it=writable.erase(it);
        if (a<lo) writable.emplace(a,lo);
        if (b>hi) { writable.emplace(hi,b); break; }
    }
}
bool page_writable(uint64_t addr) {
    auto it=writable.upper_bound(addr);
    if (it==writable.begin()) return false;
    --it;
    return it->first<=addr && addr<it->second;
}
void clear_writable_fragment(uint64_t addr,uint64_t size,uint64_t page) {
    if (!size || !page_writable(addr&~(page-1))) return;
    std::memset(reinterpret_cast<void*>(static_cast<uintptr_t>(addr)),0,
                static_cast<size_t>(size));
}

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
    if (!page || !size || addr%page || size%page ||
        addr>UINT64_MAX-size || size>static_cast<uint64_t>(SIZE_MAX) ||
        addr>static_cast<uint64_t>(UINTPTR_MAX) ||
        (size-1)>static_cast<uint64_t>(UINTPTR_MAX)-addr) return false;
    std::lock_guard<std::mutex> lock(ranges_lock);
    for (const auto& r:reservations)
        if (addr<r.end && r.first<addr+size) return false;
    // Never MAP_FIXED: it can evict unrelated memory.
    void* p=mmap(reinterpret_cast<void*>(static_cast<uintptr_t>(addr)),
                 static_cast<size_t>(size),PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if (p==MAP_FAILED) return false;
    if (reinterpret_cast<uintptr_t>(p)!=addr) {
        munmap(p,static_cast<size_t>(size)); return false;
    }
    reservations.push_back({addr,addr+size});
    return true;
}
bool commit(uint64_t addr,uint64_t size) {
    uint64_t lo=0,hi=0;
    if (!round_range(addr,size,page_bytes(),lo,hi)) return false;
    std::lock_guard<std::mutex> lock(ranges_lock);
    if (!covered(lo,hi)) return false;
    if (mprotect(reinterpret_cast<void*>(static_cast<uintptr_t>(lo)),
                 static_cast<size_t>(hi-lo),PROT_READ|PROT_WRITE)!=0) return false;
    mark_writable(lo,hi);
    return true;
}
void decommit(uint64_t addr,uint64_t size) {
    uint64_t lo=0,hi=0;
    const uint64_t page=page_bytes();
    if (!round_range(addr,size,page,lo,hi)) return;
    std::lock_guard<std::mutex> lock(ranges_lock);
    if (!covered(lo,hi)) return;
    const uint64_t end=addr+size;
    const uint64_t inner_begin=(addr+page-1)&~(page-1);
    const uint64_t inner_end=end&~(page-1);
    if (inner_begin>=inner_end) {
        // A small span may cross two pages that are protected differently.
        if ((addr&~(page-1))==((end-1)&~(page-1)))
            clear_writable_fragment(addr,size,page);
        else {
            clear_writable_fragment(addr,inner_begin-addr,page);
            clear_writable_fragment(inner_begin,end-inner_begin,page);
        }
        return;
    }
    if (addr<inner_begin) clear_writable_fragment(addr,inner_begin-addr,page);
    if (inner_end<end) clear_writable_fragment(inner_end,end-inner_end,page);
    auto it=writable.lower_bound(inner_begin);
    if (it!=writable.begin()) {
        auto prev=std::prev(it);
        if (prev->second>inner_begin) it=prev;
    }
    std::vector<Range> active;
    while (it!=writable.end() && it->first<inner_end) {
        const uint64_t a=it->first>inner_begin?it->first:inner_begin;
        const uint64_t b=it->second<inner_end?it->second:inner_end;
        if (a<b) active.push_back({a,b});
        ++it;
    }
    for (const auto& r:active) {
        void* p=reinterpret_cast<void*>(static_cast<uintptr_t>(r.first));
        const size_t n=static_cast<size_t>(r.end-r.first);
#if defined(MADV_DONTNEED)
        if (madvise(p,n,MADV_DONTNEED)!=0) std::memset(p,0,n);
#else
        std::memset(p,0,n);
#endif
        if (mprotect(p,n,PROT_NONE)==0) unmark_writable(r.first,r.end);
    }
}
} // namespace nx::plat
