// Lingshu208: one-page read-only VM inspection, NOT a Castlevania boot.
#include "virtual_query_policy.h"
#include <orbis/libkernel.h>
#include <cstdio>
extern "C" bool lingshu208_native_probe(std::FILE* log) {
    const auto result=lingshu208::run<OrbisKernelVirtualQueryInfo>(
        log,sceKernelReserveVirtualRange,sceKernelMapFlexibleMemory,
        sceKernelVirtualQuery,sceKernelMunmap);
    return result.complete;
}
