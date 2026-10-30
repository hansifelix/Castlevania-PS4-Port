// Standalone one-page PS4 flexible memory probe; no game files.
#include "flexible_policy.h"
#include <orbis/libkernel.h>
#include <cstdio>
extern "C" bool lingshu207_native_probe(std::FILE* log) {
    auto r=lingshu207::run(log,sceKernelMapFlexibleMemory,
                           sceKernelMprotect,sceKernelMunmap);
    return r.complete;
}
