// Kazuma Etapa 17: teste LIMITADO e isolado de paginas do processo homebrew.
// NAO implementa nx::plat::reserve/commit/decommit: essas interfaces exigem
// enderecos guest fixos e analise de compatibilidade separada.
#include "platform.h"
#include <sys/mman.h>
#include <cstddef>
#include <cstdint>
#include <type_traits>

static_assert(std::is_same<decltype(&nx::plat::reserve), bool(*)(uint64_t,uint64_t)>::value,
              "Contrato nx::plat::reserve alterado no upstream");
static_assert(std::is_same<decltype(&nx::plat::commit), bool(*)(uint64_t,uint64_t)>::value,
              "Contrato nx::plat::commit alterado no upstream");
static_assert(std::is_same<decltype(&nx::plat::decommit), void(*)(uint64_t,uint64_t)>::value,
              "Contrato nx::plat::decommit alterado no upstream");

extern "C" int kazuma_probe_memory_pages(void) {
    constexpr size_t size = 64u * 1024u;  // limite deliberadamente pequeno.
    void* region = mmap(nullptr, size, PROT_NONE, MAP_PRIVATE | MAP_ANON, -1, 0);
    if (region == MAP_FAILED) return 0;
    bool ok = (mprotect(region, size, PROT_READ | PROT_WRITE) == 0);
    if (ok) {
        volatile uint8_t* bytes = static_cast<volatile uint8_t*>(region);
        for (size_t i=0; i<size; i++) bytes[i]=static_cast<uint8_t>((i*13u + 17u) & 255u);
        for (size_t i=0; i<size; i++) {
            if (bytes[i] != static_cast<uint8_t>((i*13u + 17u) & 255u)) {
                ok = false;
                break;
            }
        }
    }
    // Nunca acessar bytes depois de PROT_NONE. Mesmo que os passos falhem,
    // tentar liberar a regiao mapeada para nao deixar alocacao pendente.
    if (mprotect(region, size, PROT_NONE) != 0) ok = false;
    if (munmap(region, size) != 0) ok = false;
    return ok ? 1 : 0;
}
