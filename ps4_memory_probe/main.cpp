// Programa minimo PS4 para diagnostico de APIs de memoria; NAO carrega Castlevania.
// As mensagens vao a stdout (nao aparecem na tela da TV).
#include <cstdio>
#include <orbis/libkernel.h>
#include "memory_probe.h"

int main() {
    setvbuf(stdout, nullptr, _IONBF, 0);
    std::puts("CVPS4 memory probe - aplicativo SEM JOGO");
    const std::size_t probe_sizes[] = {4096, 64u * 1024u, 1024u * 1024u};
    for (const std::size_t bytes : probe_sizes) {
        const auto r = cvps4::check_anonymous_mapping(bytes);
        std::printf("probe bytes=%zu stage=%s errno=%d addr=0x%llx\n",
                    bytes, cvps4::probe_stage_name(r.stage), r.system_errno,
                    static_cast<unsigned long long>(r.mapping_address));
    }
    // Mantem o processo aberto se futuramente for empacotado para diagnosticos na maquina.
    // A primeira etapa e somente COMPILACAO: nao ha PKG nem log legivel no console.
    for (;;) sceKernelUsleep(1000000);
}
