// Prova de contrato apenas no Linux: nao verifica APIs nem pagina real do PS4.
#include <cassert>
#include <cstdint>
#include <cstring>
#include <sys/mman.h>
#include <unistd.h>
namespace nx::plat {
  bool reserve(uint64_t, uint64_t);
  bool commit(uint64_t, uint64_t);
  void decommit(uint64_t, uint64_t);
}
int main() {
  const long p = sysconf(_SC_PAGESIZE);
  assert(p > 0);
  const size_t size = static_cast<size_t>(p) * 2;
  void* hint = mmap(nullptr,size,PROT_NONE,MAP_PRIVATE|MAP_ANON,-1,0);
  assert(hint != MAP_FAILED);
  const uint64_t a = reinterpret_cast<uintptr_t>(hint);
  assert(munmap(hint,size)==0);
  assert(!nx::plat::reserve(0,size));
  assert(!nx::plat::reserve(a+1,size));
  assert(!nx::plat::reserve(a,0));
  assert(nx::plat::reserve(a,size));
  assert(!nx::plat::reserve(a,size)); // nunca sobrescrever outra reserva
  assert(!nx::plat::commit(a+size,size)); // nunca tocar fora de reserva
  assert(nx::plat::commit(a+101,33)); // subrange parcial, arredonda para paginas
  auto* ptr = reinterpret_cast<volatile unsigned char*>(hint);
  ptr[0]=0x5A;ptr[p-1]=0x6B;
  assert(ptr[0]==0x5A && ptr[p-1]==0x6B);
  nx::plat::decommit(a,static_cast<size_t>(p));
  assert(nx::plat::commit(a,size));
  ptr[p]=0xC3;
  assert(ptr[p]==0xC3);
  assert(munmap(hint,size)==0);
  return 0;
}
