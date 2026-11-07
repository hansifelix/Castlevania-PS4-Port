#include <algorithm>  // OpenOrbis libc++ expects ::abs before <cmath>
#include <nx/cpu.h>
// Public-only synthetic ABI probe: no commercial instructions or game binaries.
extern "C" void kazuma88_probe_runtime_symbols(nx::CPU& cpu) {
    nx::call(cpu, 0x1234ull);
    nx::unimpl(cpu, 0x5678ull, "synthetic test");
}
