// Integration test of the ACTUAL tools/etapa146 virtual-memory adapter,
// compiled on Linux with a 2-line platform header and a host-only log stub.
// No commercial assets, no MAP_FIXED, no PS4 hardware claim.
#include <cassert>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <sys/mman.h>
#include <unistd.h>
#include "platform.h"

static std::string logs;
namespace nx {
void log(const char* format, ...) {
    char output[1024];
    va_list args;
    va_start(args,format);
    std::vsnprintf(output,sizeof output,format,args);
    va_end(args);
    logs.append(output);
    logs.push_back('\n');
}
}

int main() {
    const long page_len=::sysconf(_SC_PAGESIZE);
    assert(page_len>0 && (page_len&(page_len-1))==0);
    const std::uint64_t page=static_cast<std::uint64_t>(page_len);
    std::uint64_t base=0;
    // Pick a truly free host location first. ASan processes may not offer
    // the usual hardcoded guest hints; never use MAP_FIXED to force an address.
    void* probe=mmap(nullptr,static_cast<size_t>(page*16),PROT_NONE,
                     MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if(probe!=MAP_FAILED) {
        const auto hinted=static_cast<std::uint64_t>(reinterpret_cast<std::uintptr_t>(probe));
        assert(munmap(probe,static_cast<size_t>(page*16))==0);
        if(nx::plat::reserve(hinted,page*16))base=hinted;
    }
    if(!base) {
        for (auto candidate : {0x0000004000000000ull,0x0000005000000000ull,
                               0x0000006000000000ull}) {
            if (nx::plat::reserve(candidate,page*16)) {base=candidate;break;}
        }
    }
    if (!base) {
        std::puts("LINGSHU185_HOST_INTEGRATION=INCONCLUSIVE_NO_EXACT_VA");
        return 77; // Skip, not success.
    }
    // A mere PROT_NONE reservation must not be treated as writable.
    nx::plat::decommit(base,page*2);
    assert(logs.find("LINGSHU185_DECOMMIT=SKIPPED_UNCOMMITTED")!=std::string::npos);
    assert(nx::plat::commit(base,page*8));
    auto* bytes=reinterpret_cast<unsigned char*>(static_cast<uintptr_t>(base));
    std::memset(bytes,0xa5,static_cast<size_t>(page*8));
    // A committed interior page can be decommitted, then recommitted zeroed.
    nx::plat::decommit(base+page*2,page*2);
    assert(logs.find("LINGSHU185_DECOMMIT=SAFE_COMPLETED")!=std::string::npos);
    nx::plat::decommit(base+page*2,page);
    assert(nx::plat::commit(base+page*2,page*2));
    for(std::uint64_t i=page*2;i<page*4;++i) assert(bytes[i]==0);
    for(std::uint64_t i=0;i<page*2;++i) assert(bytes[i]==0xa5);
    for(std::uint64_t i=page*4;i<page*8;++i) assert(bytes[i]==0xa5);
    // Partial-page decommit preserves bytes outside the requested range.
    nx::plat::decommit(base+page*4+3,9);
    for(std::uint64_t i=0;i<page;++i) {
        const bool zero=(i>=3 && i<12);
        assert(bytes[page*4+i]==(zero?0:0xa5));
    }
    // Closing a range outside reservations must not alter the host.
    nx::plat::decommit(base+page*15,page*2);
    assert(logs.find("LINGSHU185_COMMIT=WRITABLE")!=std::string::npos);
    std::puts("LINGSHU185_REAL_ADAPTER_LINUX_MMAP=PASS_HOST_ONLY");
}
