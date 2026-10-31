#include "platform.h"
#include <sys/mman.h>
#include <unistd.h>
#include <cstdint>
#include <cstdio>
#include <cstring>
#define CHECK(x) do { if(!(x)) { std::fprintf(stderr,"FAILED %s line %d\n",#x,__LINE__);return 1; }}while(0)
int main(){
using namespace nx::plat;
long sz=sysconf(_SC_PAGESIZE); CHECK(sz>0);
uint64_t page=static_cast<uint64_t>(sz);size_t bytes=static_cast<size_t>(page*8);
void* hint=mmap(nullptr,bytes,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0); CHECK(hint!=MAP_FAILED);
uint64_t base=reinterpret_cast<uintptr_t>(hint);CHECK(munmap(hint,bytes)==0);CHECK(reserve(base,bytes));
int count=0;
decommit(base+page+8,30);++count;
decommit(base+page,page);++count;decommit(base+page+5,9);++count;
decommit(base+2*page,2*page);++count;
CHECK(commit(base+page,4*page));auto* m=reinterpret_cast<unsigned char*>(static_cast<uintptr_t>(base));
std::memset(m+page,0x5a,4*page);
decommit(base+2*page,page);++count;
decommit(base+2*page+32,64);++count;
decommit(base+page+4,16);++count;
CHECK(m[page+3]==0x5a&&m[page+4]==0&&m[page+19]==0&&m[page+20]==0x5a);++count;
CHECK(commit(base+2*page,page)); CHECK(m[2*page]==0);++count;
decommit(base+4*page+page-8,16);++count;
CHECK(m[5*page-9]==0x5a && m[5*page-8]==0);
decommit(base+2*page,3*page);++count;
decommit(base+2*page,3*page);++count;
CHECK(commit(base+page,4*page));
CHECK(m[page+3]==0x5a && m[2*page]==0 && m[3*page]==0 && m[4*page]==0);++count;
CHECK(munmap(reinterpret_cast<void*>(static_cast<uintptr_t>(base)),bytes)==0);
std::printf("LINGSHU179_REPEATED_DECOMMIT_REAL_MMAP=PASSED_%d_CASES_NO_GAME\n",count);
}
