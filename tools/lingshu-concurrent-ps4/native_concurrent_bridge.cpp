// Standalone PS4 native diagnostic bridge. NEVER linked to the game engine.
#include "concurrent_policy.h"
#include <orbis/libkernel.h>
#include <cstdio>
extern "C" bool lingshu206_native_probe(std::FILE* log) {
    const auto result=lingshu206::run(
       log,sceKernelReserveVirtualRange,sceKernelMunmap);
    return result.all_five_coexisted && result.fully_released;
}
