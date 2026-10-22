// Kazuma Port Games BR — Etapa 20
// Teste SINTETICO da ABI nx::CPU e dos acessos a memoria via nx/cpu.h.
// Nao contem codigo ARM64 recompilado de Castlevania, assets nem loader de jogo.
#include <nx/cpu.h>
#include <cstddef>
#include <cstdint>
#include <type_traits>

static_assert(sizeof(nx::V128) == 16, "V128 deveria ter 16 bytes");
static_assert(alignof(nx::V128) == 16, "V128 deveria estar alinhado a 16 bytes");
static_assert(alignof(nx::CPU) >= 16, "CPU nao atende alinhamento esperado");

// Pequeno bloco escrito por nos, no ESTILO de uma funcao que receberia nx::CPU.
// Nao e uma conversao real de instrucoes AArch64 nem prova de compatibilidade.
static void bloco_guest_sintetico(nx::CPU& cpu) {
    cpu.x[0] = cpu.x[0] + cpu.x[1];
}

extern "C" int kazuma_cpu_abi_probe() {
    nx::CPU cpu{};
    alignas(16) std::uint8_t scratch[32]{};
    cpu.x[0] = 17;
    cpu.x[1] = 25;
    bloco_guest_sintetico(cpu);
    const auto addr = static_cast<std::uint64_t>(reinterpret_cast<std::uintptr_t>(scratch));
    nx::st<std::uint64_t>(addr, cpu.x[0]);
    return (cpu.x[0] == 42 && nx::ld<std::uint64_t>(addr) == 42) ? 0 : 1;
}

int main() { return kazuma_cpu_abi_probe(); }
