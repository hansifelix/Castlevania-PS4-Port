#include "../src/ps4/memory_probe.h"

#include <cstdio>

int main() {
    using cvps4::ProbeStage;
    if (cvps4::check_anonymous_mapping(0).stage != ProbeStage::invalid_size) return 1;
    if (cvps4::check_anonymous_mapping(1024u * 1024u + 1).stage != ProbeStage::invalid_size) return 2;
    const std::size_t probe_sizes[] = {4096, 64u * 1024u, 1024u * 1024u};
    for (const std::size_t bytes : probe_sizes) {
        const auto r = cvps4::check_anonymous_mapping(bytes);
        if (r.stage != ProbeStage::ok) {
            std::printf("FALHOU: %zu bytes: %s (errno=%d)\n", bytes, cvps4::probe_stage_name(r.stage), r.system_errno);
            return 3;
        }
        std::printf("OK %zu bytes: mmap/mprotect/leitura-escrita/munmap\n", bytes);
    }
    std::puts("Todos os testes Linux de API de memoria passaram. Isso NAO prova compatibilidade com PS4 ou com o jogo.");
    return 0;
}
