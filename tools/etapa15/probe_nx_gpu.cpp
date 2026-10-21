// Usa apenas funcao pura do runtime publico; candidatos SIMULADOS. Nao e driver GPU PS4.
#include "nvn_gpu_pick.h"
#include <vector>
#include <string>
#include <cstdio>
extern "C" int kazuma_probe_upstream(void) {
    const std::vector<nx::nvn::GpuCandidate> fake = {
        {"integrated test adapter",1}, {"discrete test adapter",2}
    };
    bool matched=false;
    const auto selected=nx::nvn::pick_gpu(fake,"discrete",matched);
    const bool pass=(matched && selected==1);
    std::printf("KAZUMA STAGE14: nx::nvn::pick_gpu sintentico: %s\n", pass ? "PASS" : "FAIL");
    return pass ? 1 : 0;
}
