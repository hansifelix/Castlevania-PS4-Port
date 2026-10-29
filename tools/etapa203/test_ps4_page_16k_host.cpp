// Stage 203: real stage146 PS4 adapter tested with simulated 16-KiB pages.
// Only a 64-KiB host allocation; the adapter's mmap is wrapped to return it.
// No 4–64 GiB reservations, game files or PlayStation kernel calls.
#include "platform.h"
#include <cassert>
#include <cerrno>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <sys/mman.h>
#include <unistd.h>

namespace {
constexpr std::size_t kPage=16384;
constexpr std::size_t kPages=2;
std::uintptr_t guest_base=0;
unsigned reserve_calls=0;
std::string log_output;
}
namespace nx {
void log(const char* fmt, ...) {
    char buffer[1024];
    va_list ap;
    va_start(ap, fmt);
    std::vsnprintf(buffer, sizeof(buffer), fmt, ap);
    va_end(ap);
    log_output+=buffer;
    log_output+='\n';
}
}
extern "C" long __real_sysconf(int);
extern "C" long __wrap_sysconf(int name) {
    if(name==_SC_PAGESIZE) return static_cast<long>(kPage);
    return __real_sysconf(name);
}
extern "C" void* __real_mmap(void*,size_t,int,int,int,off_t);
extern "C" void* __wrap_mmap(void* p,size_t n,int prot,int flags,int fd,off_t off) {
    (void)fd; (void)off;
    assert(reinterpret_cast<std::uintptr_t>(p)==guest_base);
    assert(n==kPage*kPages && prot==PROT_NONE);
    assert((flags&MAP_PRIVATE) && (flags&MAP_ANONYMOUS));
    ++reserve_calls;
    return p; // test preallocated this small host range
}
int main() {
    // Extra alignment space, no MAP_FIXED.
    const size_t extent=kPage*4;
    void* raw=__real_mmap(nullptr,extent,PROT_READ|PROT_WRITE,
                          MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    assert(raw!=MAP_FAILED);
    const auto start=reinterpret_cast<std::uintptr_t>(raw);
    guest_base=(start+kPage-1)&~std::uintptr_t(kPage-1);
    assert(guest_base>=start && guest_base+kPage*kPages<=start+extent);
    auto* p=reinterpret_cast<unsigned char*>(guest_base);
    assert(::mprotect(p,kPage*kPages,PROT_NONE)==0);
    assert(nx::plat::reserve(guest_base,kPage*kPages));
    assert(reserve_calls==1);

    // 4-KiB guest commit activates one 16-KiB PS4 page.
    assert(nx::plat::commit(guest_base+4096,4096));
    std::memset(p,0xA5,kPage);
    assert(nx::plat::commit(guest_base+8192,4096));
    nx::plat::decommit(guest_base+4096,4096);
    for(std::size_t i=0;i<kPage;++i)
        assert(p[i]==((i>=4096 && i<8192)?0:0xA5));
    assert(nx::plat::commit(guest_base+kPage,kPage));
    std::memset(p+kPage,0x6C,kPage);

    // A decommit across two partial 16-KiB pages must preserve neighbors.
    nx::plat::decommit(guest_base+kPage-4096,8192);
    for(std::size_t i=0;i<kPage;++i) {
        unsigned char expected=(i>=4096&&i<8192)?0:0xA5;
        if(i>=kPage-4096)expected=0;
        assert(p[i]==expected);
    }
    for(std::size_t i=0;i<kPage;++i)
        assert(p[kPage+i]==(i<4096?0:0x6C));

    // A whole page is discarded and recommitted as zeroes.
    nx::plat::decommit(guest_base+kPage,kPage);
    assert(nx::plat::commit(guest_base+kPage,kPage));
    for(std::size_t i=0;i<kPage;++i)assert(p[kPage+i]==0);
    assert(p[0]==0xA5 && p[kPage-1]==0);
    assert(log_output.find("LINGSHU185_DECOMMIT=SAFE_COMPLETED")!=std::string::npos);
    assert(::munmap(raw,extent)==0);
    std::puts("LINGSHU203_REAL_ADAPTER_16K_PAGE=PASS_HOST_ONLY_NOT_PS4");
}
