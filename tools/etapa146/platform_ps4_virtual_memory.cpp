// LINGSHU LAB 146 — fail-closed provisional PS4 virtual-memory adapter.
// The host uses fixed guest addresses. Never overwrite pre-existing mappings.
// IMPORTANT: compilation is NOT hardware validation. Large fixed guest ranges
// may be unavailable on actual PS4 and must be checked before boot attempts.
#include "platform.h"
#include "../etapa185/page_commit_ledger.h"
#include <nx/runtime.h>
#include <cerrno>
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
lingshu185::CommitLedger committed_pages; // guarded by ranges_lock
// A failed cleanup of a relocated mmap leaves unknown mappings behind.
// Do not perform further guest-memory operations in this process.
bool address_space_uncertain = false; // guarded by ranges_lock

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
        addr>std::numeric_limits<uint64_t>::max()-size) {
        nx::log("LINGSHU184_VM=INVALID_RANGE addr=%llx bytes=%llu page=%llu",
                (unsigned long long)addr,(unsigned long long)size,
                (unsigned long long)page);
        return false;
    }
    if (size>static_cast<uint64_t>(SIZE_MAX) ||
        addr>static_cast<uint64_t>(UINTPTR_MAX)) {
        nx::log("LINGSHU184_VM=UNREPRESENTABLE addr=%llx bytes=%llu",
                (unsigned long long)addr,(unsigned long long)size);
        return false;
    }
    std::lock_guard<std::mutex> lock(ranges_lock);
    if (address_space_uncertain) {
        nx::log("LINGSHU202_VM=QUARANTINED_RESERVE_STOP");
        return false;
    }
    for (const auto& r:reservations)
        if (addr<r.end && r.first<addr+size) {
            nx::log("LINGSHU184_VM=ALREADY_RESERVED addr=%llx bytes=%llu",
                    (unsigned long long)addr,(unsigned long long)size);
            return false;
        }
    nx::log("LINGSHU184_VM=REQUEST addr=%llx bytes=%llu flags=HINT_NON_FIXED",
            (unsigned long long)addr,(unsigned long long)size);
    errno=0;
    void* result=mmap(reinterpret_cast<void*>(static_cast<uintptr_t>(addr)),
                      static_cast<size_t>(size), PROT_NONE,
                      MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if (result==MAP_FAILED) {
        const int saved_errno=errno;
        nx::log("LINGSHU184_VM=MMAP_FAILED addr=%llx bytes=%llu errno=%d",
                (unsigned long long)addr,(unsigned long long)size,saved_errno);
        return false;
    }
    const uint64_t actual=static_cast<uint64_t>(reinterpret_cast<uintptr_t>(result));
    if (actual!=addr) {
        const int unmap_status=munmap(result,static_cast<size_t>(size));
        const int saved_errno=unmap_status==0?0:errno;
        if (unmap_status != 0) {
            // The returned range may still be mapped. Never continue blindly.
            address_space_uncertain = true;
            nx::log("LINGSHU202_VM=RELOCATED_CLEANUP_FAILED_QUARANTINE errno=%d",
                    saved_errno);
        }
        nx::log("LINGSHU184_VM=RELOCATED_REJECTED requested=%llx actual=%llx bytes=%llu unmap_rc=%d errno=%d",
                (unsigned long long)addr,(unsigned long long)actual,
                (unsigned long long)size,unmap_status,saved_errno);
        return false;
    }
    reservations.push_back({addr,addr+size});
    nx::log("LINGSHU184_VM=EXACT_RESERVED addr=%llx bytes=%llu",
            (unsigned long long)addr,(unsigned long long)size);
    return true;
}

bool commit(uint64_t addr,uint64_t size) {
    uint64_t lo=0,hi=0;
    if (!round_range(addr,size,page_bytes(),lo,hi)) {
        nx::log("LINGSHU185_COMMIT=INVALID_RANGE addr=%llx bytes=%llu",
                (unsigned long long)addr,(unsigned long long)size);
        return false;
    }
    std::lock_guard<std::mutex> lock(ranges_lock);
    if (address_space_uncertain) {
        nx::log("LINGSHU202_VM=QUARANTINED_COMMIT_STOP");
        return false;
    }
    if (!covered(lo,hi)) {
        nx::log("LINGSHU185_COMMIT=OUTSIDE_RESERVATION addr=%llx bytes=%llu",
                (unsigned long long)addr,(unsigned long long)size);
        return false;
    }
    errno=0;
    if (mprotect(reinterpret_cast<void*>(static_cast<uintptr_t>(lo)),
                 static_cast<size_t>(hi-lo),PROT_READ|PROT_WRITE)!=0) {
        const int saved_errno=errno;
        nx::log("LINGSHU185_COMMIT=MPROTECT_FAILED addr=%llx bytes=%llu errno=%d",
                (unsigned long long)lo,(unsigned long long)(hi-lo),saved_errno);
        return false;
    }
    // Mark pages writable ONLY AFTER successful mprotect; never infer this
    // from a prior successful PROT_NONE reservation.
    committed_pages.add(lo,hi);
    nx::log("LINGSHU185_COMMIT=WRITABLE addr=%llx bytes=%llu",
            (unsigned long long)lo,(unsigned long long)(hi-lo));
    return true;
}

void decommit(uint64_t addr,uint64_t size) {
    uint64_t lo=0,hi=0;
    const uint64_t page=page_bytes();
    if (!round_range(addr,size,page,lo,hi)) {
        nx::log("LINGSHU185_DECOMMIT=INVALID_RANGE addr=%llx bytes=%llu",
                (unsigned long long)addr,(unsigned long long)size);
        return;
    }
    std::lock_guard<std::mutex> lock(ranges_lock);
    if (address_space_uncertain) {
        nx::log("LINGSHU202_VM=QUARANTINED_DECOMMIT_STOP");
        return;
    }
    if (!covered(lo,hi) || !committed_pages.covers(lo,hi)) {
        // Before stage 185, this path could call memset() on PROT_NONE pages
        // and crash the host process. Skip rather than touching unknown pages.
        nx::log("LINGSHU185_DECOMMIT=SKIPPED_UNCOMMITTED addr=%llx bytes=%llu",
                (unsigned long long)addr,(unsigned long long)size);
        return;
    }

    // Preserve adjacent live allocations sharing the first or last page.
    // Only whole interior pages can be changed back to PROT_NONE.
    const uint64_t end=addr+size;
    const uint64_t inner_begin=(addr+page-1)&~(page-1);
    const uint64_t inner_end=end & ~(page-1);
    if (inner_begin < inner_end) {
        void* ptr=reinterpret_cast<void*>(static_cast<uintptr_t>(inner_begin));
        const size_t count=static_cast<size_t>(inner_end-inner_begin);
#if defined(MADV_DONTNEED)
        errno=0;
        if (madvise(ptr,count,MADV_DONTNEED)!=0) {
            const int saved_errno=errno;
            nx::log("LINGSHU185_DECOMMIT=MADVISE_FAILED addr=%llx bytes=%llu errno=%d",
                    (unsigned long long)inner_begin,(unsigned long long)count,saved_errno);
            return;  // Never fall back to giant unsafe memset.
        }
        errno=0;
        if (mprotect(ptr,count,PROT_NONE)!=0) {
            const int saved_errno=errno;
            // MADV_DONTNEED has already discarded the contents. Returning
            // with the old ledger would let the guest continue using pages
            // whose memory state is no longer trustworthy. Block subsequent
            // operations rather than pretending this decommit was harmless.
            address_space_uncertain = true;
            nx::log("LINGSHU204_VM=DECOMMIT_MPROTECT_FAILED_AFTER_MADVISE_QUARANTINE errno=%d",
                    saved_errno);
            nx::log("LINGSHU185_DECOMMIT=MPROTECT_FAILED addr=%llx bytes=%llu errno=%d",
                    (unsigned long long)inner_begin,(unsigned long long)count,saved_errno);
            return;
        }
        committed_pages.remove(inner_begin,inner_end);
#else
        nx::log("LINGSHU185_DECOMMIT=UNSUPPORTED_NO_MADV_DONTNEED addr=%llx bytes=%llu",
                (unsigned long long)inner_begin,(unsigned long long)count);
        return;  // Fail closed; do not leave decommitted pages readable.
#endif
    }
    // Only write partial head/tail bytes; page protection remains RW there.
    // The ledger's covers() condition above guarantees both are writable.
    const uint64_t head_end=std::min(end,inner_begin);
    if (addr < head_end)
        std::memset(reinterpret_cast<void*>(static_cast<uintptr_t>(addr)),0,
                    static_cast<size_t>(head_end-addr));
    const uint64_t tail_begin=std::max(head_end,inner_end);
    if (tail_begin < end)
        std::memset(reinterpret_cast<void*>(static_cast<uintptr_t>(tail_begin)),0,
                    static_cast<size_t>(end-tail_begin));
    nx::log("LINGSHU185_DECOMMIT=SAFE_COMPLETED addr=%llx bytes=%llu",
            (unsigned long long)addr,(unsigned long long)size);
}
} // namespace nx::plat
