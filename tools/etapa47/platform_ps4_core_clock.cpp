// Kazuma - Etapa 47. Temporizacao nativa PS4 (experimental).
// A Etapa 46 mediu nanosleep(2ms) como 1-22us. Nao presumir que esse relogio
// POSIX e confiavel para benchmarking no PS4.
// Implementa as tres APIs nx::plat sem mudar a Etapa 38 nem seus historicos.
#include "platform.h"
#include "clock_math.h"
#include <orbis/libkernel.h>
#include <cstdint>
#include <cstdio>
#include <limits>

namespace nx::plat {
void log_line(const char* line) {
    if (!line) return;
    std::fprintf(stderr, "%s\n", line);
    std::fflush(stderr);
}

uint64_t monotonic_ns() {
    const uint64_t freq = sceKernelGetProcessTimeCounterFrequency();
    const uint64_t ticks = sceKernelGetProcessTimeCounter();
    return kazuma47::ticks_to_ns(ticks, freq);
}

void sleep_ns(int64_t ns) {
    if (ns <= 0) return;
    // OpenOrbis define sceKernelUsleep em microssegundos (nao nanossegundos).
    uint64_t micros = kazuma47::round_ns_to_us(static_cast<uint64_t>(ns));
    while (micros) {
        const uint32_t part = static_cast<uint32_t>(micros > 1000000ull ? 1000000ull : micros);
        if (sceKernelUsleep(part) != 0) return; // nao esconder erros no adaptador
        micros -= part;
    }
}
} // namespace nx::plat
