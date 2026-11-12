// PS4 providers for optional runtime services whose upstream contract explicitly
// permits an unsupported/zero result on hosts without these facilities.
// No profiler or memory-guard timing is fabricated on the console.
#include <platform.h>

namespace nx::plat {

bool headless() {
    // The PS4 target has no desktop hidden-window mode in this port.
    return false;
}

uint64_t memguard_overlap_ns(uint64_t from, uint64_t to) {
    // Upstream contract: zero on hosts without the platform memory guard.
    (void)from;
    (void)to;
    return 0;
}

bool profile(const int64_t* tids,
             const uint64_t* const* guest_lr,
             size_t count,
             int seconds,
             const std::string& path) {
    // Explicitly unsupported: do not claim profiling data was collected.
    (void)tids;
    (void)guest_lr;
    (void)count;
    (void)seconds;
    (void)path;
    return false;
}

} // namespace nx::plat
