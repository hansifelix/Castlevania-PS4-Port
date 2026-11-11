// Stage 204: actual platform_ps4_virtual_memory.cpp under simulated OS calls.
// Tests a decommit whose MADV_DONTNEED succeeds but mprotect(PROT_NONE) fails.
// NO real guest mappings and NO game data or PS4 hardware access.
#include "platform.h"
#include <cassert>
#include <cerrno>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <string>
#include <sys/mman.h>

namespace {
constexpr std::uint64_t kPage=4096;
constexpr std::uint64_t kBase=0x0000000200000000ull;
std::string logs;
unsigned map_calls=0, protect_calls=0, advise_calls=0;
bool fail_advise=false;
bool fail_decommit_protection=false;
}
namespace nx {
void log(const char* fmt,...) {
    char b[1024];
    va_list ap;
    va_start(ap,fmt);
    std::vsnprintf(b,sizeof b,fmt,ap);
    va_end(ap);
    logs+=b;
    logs+='\n';
}
}
extern "C" void* __wrap_mmap(void* requested, size_t size, int prot,
                             int flags, int fd, off_t offset) {
    (void)fd;(void)offset;
    assert(size==2*kPage);
    assert(prot==PROT_NONE && (flags & MAP_ANONYMOUS) && (flags & MAP_PRIVATE));
    ++map_calls;
    return requested; // pretend exact guest VA; never dereference in this test
}
extern "C" int __wrap_mprotect(void*,size_t count,int prot) {
    assert(count==kPage || count==2*kPage);
    ++protect_calls;
    if(prot==PROT_NONE && fail_decommit_protection) {
        errno=EACCES;
        return -1;
    }
    assert(prot==PROT_NONE || prot==(PROT_READ|PROT_WRITE));
    return 0;
}
extern "C" int __wrap_madvise(void*,size_t count,int action) {
    assert(action==MADV_DONTNEED && count==kPage);
    ++advise_calls;
    if(fail_advise) {errno=EIO;return -1;}
    return 0; // OS might now have discarded guest page contents
}
int main() {
    assert(nx::plat::reserve(kBase,2*kPage));
    assert(nx::plat::commit(kBase,2*kPage));
    assert(map_calls==1 && protect_calls==1);

    // A failed madvise cannot be mistaken for a successful decommit;
    // the previous path only logs failure and doesn't change ledger.
    fail_advise=true;
    nx::plat::decommit(kBase,kPage);
    assert(logs.find("LINGSHU185_DECOMMIT=MADVISE_FAILED")!=std::string::npos);
    assert(advise_calls==1 && protect_calls==1);
    fail_advise=false;
    assert(nx::plat::commit(kBase,kPage));
    assert(protect_calls==2); // no quarantine on early madvise failure

    // MADV_DONTNEED succeeds; protection fails: now the contents are
    // potentially discarded while the internal ledger remains committed.
    fail_decommit_protection=true;
    nx::plat::decommit(kBase,kPage);
    assert(advise_calls==2 && protect_calls==3);
    assert(logs.find("LINGSHU204_VM=DECOMMIT_MPROTECT_FAILED_AFTER_MADVISE_QUARANTINE errno=13")!=std::string::npos);
    assert(logs.find("LINGSHU185_DECOMMIT=MPROTECT_FAILED")!=std::string::npos);

    // Quarantine must stop all additional OS mapping operations.
    assert(!nx::plat::reserve(kBase+0x10000,2*kPage));
    assert(!nx::plat::commit(kBase,kPage));
    nx::plat::decommit(kBase,kPage);
    assert(map_calls==1 && protect_calls==3 && advise_calls==2);
    assert(logs.find("LINGSHU202_VM=QUARANTINED_RESERVE_STOP")!=std::string::npos);
    assert(logs.find("LINGSHU202_VM=QUARANTINED_COMMIT_STOP")!=std::string::npos);
    assert(logs.find("LINGSHU202_VM=QUARANTINED_DECOMMIT_STOP")!=std::string::npos);
    std::puts("LINGSHU204_DECOMMIT_MPROTECT_FAILURE_QUARANTINE=PASS_HOST_ONLY_NOT_PS4");
}
