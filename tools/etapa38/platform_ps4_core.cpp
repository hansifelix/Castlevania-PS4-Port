// Kazuma, Etapa 38. Adaptador MINIMO, experimental e auditavel para OpenOrbis.
// Nao faz reserva de memoria, audio, controles ou apresentacao Vulkan.
// Compilacao offline apenas: nao executar como runtime do jogo.
#include "platform.h"   // interface publica do runtime NVN (commit fixado no workflow)
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <ctime>

namespace nx::plat {
void log_line(const char* line) {
    if (!line) return;
    std::fprintf(stderr, "%s\n", line);
    std::fflush(stderr);
}

uint64_t monotonic_ns() {
    timespec ts{};
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) return 0;
    return uint64_t(ts.tv_sec) * 1000000000ull + uint64_t(ts.tv_nsec);
}

void sleep_ns(int64_t ns) {
    if (ns <= 0) return;
    timespec req{time_t(ns / 1000000000ll), long(ns % 1000000000ll)};
    while (nanosleep(&req, &req) != 0 && errno == EINTR) {}
}
}  // namespace nx::plat
