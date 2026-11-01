// Injected POSIX failures exercise the actual production VM adapter.
// Linked with --wrap; the adapter code itself is not mocked.
// A separate process runs each case so the fail-closed state starts clean.
#include "platform.h"
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string_view>
#include <sys/mman.h>
#include <unistd.h>

namespace {
bool deny_madvise = false;
bool deny_reprotect = false;
bool deny_cleanup = false;
int madvise_hits = 0;
int reprotect_hits = 0;
int cleanup_hits = 0;
#define CHECK(x) do { if (!(x)) { \
    std::fprintf(stderr,"LINGSHU179_FAILURE_TEST failed: %s at line %d\\n",#x,__LINE__); \
    return 1; } } while (0)
}

extern "C" int __real_madvise(void*, size_t, int);
extern "C" int __real_mprotect(void*, size_t, int);
extern "C" int __real_munmap(void*, size_t);

extern "C" int __wrap_madvise(void* p, size_t size, int advice) {
    if (deny_madvise && advice == MADV_DONTNEED) {
        ++madvise_hits;
        errno = EIO;
        return -1;
    }
    return __real_madvise(p,size,advice);
}
extern "C" int __wrap_mprotect(void* p, size_t size, int prot) {
    if (deny_reprotect && prot == PROT_NONE) {
        ++reprotect_hits;
        errno = EACCES;
        return -1;
    }
    return __real_mprotect(p,size,prot);
}
extern "C" int __wrap_munmap(void* p, size_t size) {
    if (deny_cleanup) {
        ++cleanup_hits;
        // Release the host allocation anyway, but report failure to the
        // adapter as if the kernel could not guarantee cleanup.
        const int result = __real_munmap(p,size);
        if (result == 0) { errno = EIO; return -1; }
        return result;
    }
    return __real_munmap(p,size);
}

int main(int argc,char** argv) {
    CHECK(argc==2);
    const std::string_view mode(argv[1]);
    const long sz=sysconf(_SC_PAGESIZE);
    CHECK(sz>0);
    const size_t page=static_cast<size_t>(sz);
    const size_t bytes=4*page;

    if (mode=="cleanup") {
        void* occupied=mmap(nullptr,page,PROT_READ|PROT_WRITE,
                            MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
        CHECK(occupied!=MAP_FAILED);
        auto* sentinel=static_cast<unsigned char*>(occupied);
        sentinel[0]=0x7a;
        deny_cleanup=true;
        // Non-fixed mmap cannot reuse 'occupied', hence the adapter's
        // mismatch cleanup path is guaranteed to be exercised.
        CHECK(!nx::plat::reserve(reinterpret_cast<uintptr_t>(occupied),page));
        deny_cleanup=false;
        CHECK(cleanup_hits==1 && sentinel[0]==0x7a);
        void* fresh=mmap(nullptr,page,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
        CHECK(fresh!=MAP_FAILED);
        const uint64_t addr=reinterpret_cast<uintptr_t>(fresh);
        CHECK(munmap(fresh,page)==0);
        CHECK(!nx::plat::reserve(addr,page)); // poisoned until restart
        CHECK(munmap(occupied,page)==0);
        std::puts("LINGSHU179_FAIL_CLOSED_MUNMAP=PASSED");
        return 0;
    }

    void* hint=mmap(nullptr,bytes,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    CHECK(hint!=MAP_FAILED);
    const uint64_t base=reinterpret_cast<uintptr_t>(hint);
    CHECK(munmap(hint,bytes)==0);
    CHECK(nx::plat::reserve(base,bytes));
    CHECK(nx::plat::commit(base,bytes));
    auto* mem=reinterpret_cast<unsigned char*>(static_cast<uintptr_t>(base));
    std::memset(mem,0x6b,bytes);
    if (mode=="advice") {
        deny_madvise=true;
        nx::plat::decommit(base+page,page);
        deny_madvise=false;
        CHECK(madvise_hits==1);
        CHECK(nx::plat::commit(base+page,page));
        CHECK(mem[page]==0 && mem[page+page-1]==0);
        CHECK(mem[0]==0x6b && mem[2*page]==0x6b);
        std::puts("LINGSHU179_MADVISE_FALLBACK=PASSED");
    } else if (mode=="reprotect") {
        deny_reprotect=true;
        nx::plat::decommit(base+page,page);
        deny_reprotect=false;
        CHECK(reprotect_hits==1);
        CHECK(!nx::plat::commit(base+2*page,page)); // fail closed
        nx::plat::decommit(base+2*page,page);       // harmless no-op
        CHECK(!nx::plat::reserve(base+bytes, page));
        std::puts("LINGSHU179_FAIL_CLOSED_MPROTECT=PASSED");
    } else {
        std::fprintf(stderr,"unknown test mode: %s\\n",argv[1]);
        return 2;
    }
    CHECK(munmap(reinterpret_cast<void*>(static_cast<uintptr_t>(base)),bytes)==0);
    return 0;
}
