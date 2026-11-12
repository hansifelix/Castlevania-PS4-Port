// Native PS4 implementation of nx::plat::set_thread_name.
// Uses libkernel directly and aborts on a real API error instead of claiming success.
#include <platform.h>
#include <cstdlib>

#if !defined(KAZUMA_PS4_NATIVE)
#error "This provider must be compiled for the native PS4 target"
#endif
#include <orbis/libkernel.h>

namespace nx::plat {
void set_thread_name(const char* name) {
    if (!name || !*name) return;
    if (scePthreadRename(scePthreadSelf(), name) != 0) std::abort();
}
} // namespace nx::plat
