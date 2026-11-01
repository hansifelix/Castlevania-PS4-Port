// Fault injection against the actual adapter; Linux only, no game bytes.
#include <cassert>
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <sys/mman.h>
#include <unistd.h>
namespace nx::plat {bool reserve(uint64_t,uint64_t);bool commit(uint64_t,uint64_t);void decommit(uint64_t,uint64_t);}
static int advice_calls=0,protect_calls=0;
extern "C" int __real_madvise(void*,size_t,int);
extern "C" int __wrap_madvise(void*,size_t,int) {
  ++advice_calls; errno=EIO; return -1;
}
extern "C" int __real_mprotect(void*,size_t,int);
extern "C" int __wrap_mprotect(void* p,size_t n,int prot) {
  ++protect_calls; return __real_mprotect(p,n,prot);
}
int main(){
  const auto pg=static_cast<uint64_t>(sysconf(_SC_PAGESIZE));
  void* probe=mmap(nullptr,pg*4,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
  assert(probe!=MAP_FAILED);
  const auto addr=static_cast<uint64_t>(reinterpret_cast<uintptr_t>(probe));
  assert(munmap(probe,pg*4)==0);
  if(!nx::plat::reserve(addr,pg*4)){puts("INCONCLUSIVE_EXACT_ADDRESS_UNAVAILABLE");return 77;}
  assert(nx::plat::commit(addr,pg*4));
  nx::plat::decommit(addr,pg*4);
  assert(advice_calls==1);
  assert(!nx::plat::commit(addr,pg)); // Quarantined, no further syscalls.
  assert(protect_calls==1);
  puts("LINGSHU_VM_MADVISE_FAILURE_QUARANTINE=PASS_HOST_ONLY");
}
