#include "platform.h"
#include <sys/mman.h>
#include <unistd.h>
#include <array>
#include <vector>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>

// 5000 real mmap/mprotect/madvise operations checked against byte-for-byte
// reference data, without touching protected pages. No game involved.
static uint64_t seed=0x179179A0BEEF4321ULL;
static uint64_t rnd(){seed ^= seed<<13; seed ^= seed>>7; seed ^= seed<<17; return seed;}
#define VERIFY(x) do {if(!(x)){std::fprintf(stderr,"STRESS179_FAIL line %d op=%zu\n",__LINE__, op);return 1;}}while(0)
int main(){
    constexpr size_t pages=12;
    const long ps=sysconf(_SC_PAGESIZE);
    if(ps<=0) return 2;
    const size_t page=static_cast<size_t>(ps);
    const size_t bytes=pages*page;
    void* hint=mmap(nullptr,bytes,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if(hint==MAP_FAILED) return 3;
    const uint64_t base=reinterpret_cast<uintptr_t>(hint);
    if(munmap(hint,bytes)!=0 || !nx::plat::reserve(base,bytes)) return 4;
    auto* ptr=reinterpret_cast<unsigned char*>(static_cast<uintptr_t>(base));
    std::vector<unsigned char> expected(bytes,0);
    std::array<bool,pages> writeable{};
    for(size_t op=0;op<5000;++op){
        const size_t offset=static_cast<size_t>(rnd()%bytes);
        const size_t avail=bytes-offset;
        const size_t len=1+static_cast<size_t>(rnd()%std::min(avail,page*3));
        const size_t lo=offset/page;
        const size_t hi=(offset+len-1)/page;
        switch(rnd()%3){
        case 0: {
            VERIFY(nx::plat::commit(base+offset,len));
            for(size_t p=lo;p<=hi;++p) writeable[p]=true;
            break;
        }
        case 1: {
            nx::plat::decommit(base+offset,len);
            for(size_t p=lo;p<=hi;++p){
                const size_t first=std::max(offset,p*page);
                const size_t end=std::min(offset+len,(p+1)*page);
                if(!writeable[p]) continue;
                if(first==p*page && end==(p+1)*page){
                    std::fill(expected.begin()+p*page, expected.begin()+(p+1)*page,0);
                    writeable[p]=false;
                } else {
                    std::fill(expected.begin()+first, expected.begin()+end,0);
                }
            }
            break;
        }
        default: {
            const size_t at=offset;
            if(writeable[lo]){
                const unsigned char v=static_cast<unsigned char>(rnd());
                ptr[at]=v; expected[at]=v;
            }
            break;
        }
        }
        for(size_t p=0;p<pages;++p) if(writeable[p]){
            VERIFY(std::memcmp(ptr+p*page,expected.data()+p*page,page)==0);
        }
    }
    if(munmap(reinterpret_cast<void*>(static_cast<uintptr_t>(base)),bytes)!=0) return 5;
    std::puts("LINGSHU179_MEMORY_STRESS=PASSED_5000_REAL_SYSCALL_OPERATIONS_NO_GAME");
}
