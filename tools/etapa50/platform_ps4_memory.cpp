// Kazuma Etapa 50 — adaptador conservador de memoria virtual para nx::plat.
// Este arquivo SOMENTE e compilado para PS4 no GitHub. Nao foi executado no PS4.
// NUNCA usa MAP_FIXED: a reserva tem de ocorrer exatamente no endereco desejado,
// sem sobrescrever mapeamentos pre-existentes do sistema ou de outros componentes.
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <sys/mman.h>
#include <unistd.h>

namespace nx::plat {
namespace {
constexpr size_t kSlots = 128;
struct Region { uint64_t start, size; };
Region regions[kSlots] = {};
std::atomic_flag region_lock = ATOMIC_FLAG_INIT;

struct Guard {
  Guard() { while (region_lock.test_and_set(std::memory_order_acquire)) {} }
  ~Guard() { region_lock.clear(std::memory_order_release); }
  Guard(const Guard&) = delete;
  Guard& operator=(const Guard&) = delete;
};

uint64_t page_size() {
  const long p = sysconf(_SC_PAGESIZE);
  // NUNCA supor 4 KiB no PS4; exigir pagina real do SO.
  if (p < 4096 || (static_cast<unsigned long>(p) & (p - 1)) != 0) return 0;
  return static_cast<uint64_t>(p);
}

bool valid_range(uint64_t addr, uint64_t size) {
  return addr >= 0x10000 && size != 0 && addr <= UINT64_MAX - size &&
         size <= static_cast<uint64_t>(std::numeric_limits<size_t>::max());
}

bool contained(uint64_t addr, uint64_t size) {
  const uint64_t end = addr + size;  // requires valid_range first
  for (const auto& r : regions) {
    if (r.size && addr >= r.start && end <= r.start + r.size) return true;
  }
  return false;
}

bool aligned_region(uint64_t addr, uint64_t size, uint64_t page) {
  return valid_range(addr,size) && page && addr % page == 0 && size % page == 0;
}

bool aligned_subrange(uint64_t addr,uint64_t size,uint64_t page,
                      uint64_t& start,uint64_t& len) {
  if (!valid_range(addr,size) || !page) return false;
  start = addr - addr % page;
  const uint64_t end = addr + size;
  if (end > UINT64_MAX - (page - 1)) return false;
  const uint64_t rounded_end = (end + page - 1) & ~(page - 1);
  if (rounded_end <= start) return false;
  len = rounded_end - start;
  if (len > static_cast<uint64_t>(std::numeric_limits<size_t>::max())) return false;
  return true;
}
} // namespace

bool reserve(uint64_t addr, uint64_t size) {
  const uint64_t page = page_size();
  if (!aligned_region(addr,size,page)) return false;
  {
    Guard guard;
    size_t slot = kSlots;
    for (size_t i=0;i<kSlots;i++) {
      if (regions[i].size == 0) {slot=i;break;}
    }
    if (slot==kSlots) return false;
    // MAP_FIXED seria perigoso; mapa como dica e verifica endereco EXATO.
    void* result = mmap(reinterpret_cast<void*>(static_cast<uintptr_t>(addr)),
        static_cast<size_t>(size), PROT_NONE, MAP_PRIVATE | MAP_ANON, -1, 0);
    if (result == MAP_FAILED) return false;
    if (reinterpret_cast<uintptr_t>(result) != addr) {
      munmap(result, static_cast<size_t>(size));
      return false;
    }
    regions[slot] = Region{addr,size};
  }
  return true;
}

bool commit(uint64_t addr, uint64_t size) {
  const uint64_t page = page_size();
  uint64_t start=0,len=0;
  if (!aligned_subrange(addr,size,page,start,len)) return false;
  Guard guard;
  if (!contained(start,len)) return false; // nao tocar memoria nao pertencente ao adaptador
  return mprotect(reinterpret_cast<void*>(static_cast<uintptr_t>(start)),
                  static_cast<size_t>(len), PROT_READ | PROT_WRITE) == 0;
}

void decommit(uint64_t addr, uint64_t size) {
  const uint64_t page = page_size();
  uint64_t start=0,len=0;
  if (!aligned_subrange(addr,size,page,start,len)) return;
  Guard guard;
  if (!contained(start,len)) return;
  void* ptr = reinterpret_cast<void*>(static_cast<uintptr_t>(start));
  // Primeiro remover o acesso. madvise nao e garantia de liberacao fisica.
  if (mprotect(ptr, static_cast<size_t>(len), PROT_NONE) == 0) {
    (void)madvise(ptr, static_cast<size_t>(len), MADV_DONTNEED);
  }
}
} // namespace nx::plat
