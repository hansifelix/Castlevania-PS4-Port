#pragma once

#include <cstddef>
#include <cstdint>

namespace cvps4 {

// Diagnostico LIMITADO de memoria virtual. Nao reserva os enderecos do Switch.
enum class ProbeStage : int {
    ok = 0,
    invalid_size = 1,
    mmap_failed = 2,
    mprotect_failed = 3,
    data_mismatch = 4,
    munmap_failed = 5,
};

struct MemoryProbeResult {
    ProbeStage stage;
    int system_errno;
    std::uintptr_t mapping_address; // Apenas informativo; nunca reutilizar como endereco fixo.
    std::size_t bytes;
};

// Testa protecao/copia de ate 1 MiB em enderecos escolhidos PELO SISTEMA.
// Nao usa MAP_FIXED, nao executa codigo dinamico, nem altera outros processos.
MemoryProbeResult check_anonymous_mapping(std::size_t bytes);

const char* probe_stage_name(ProbeStage stage);

} // namespace cvps4
