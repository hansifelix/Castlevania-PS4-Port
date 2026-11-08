// Kazuma Traducoes: PS4 host time/thread primitives for the MIT nx runtime.
// These are real operating system calls; no synthetic clock or fake thread ID.
// Does NOT implement the separate thread creation / stack-size contract.
#include <platform.h>
#include <cerrno>
#include <cstdint>
#include <limits>
#include <sched.h>
#include <time.h>

#if defined(__FreeBSD__)
#include <orbis/libkernel.h>  // real Sony PS4 import: scePthreadGetthreadid
#elif defined(__linux__)
#include <sys/syscall.h>
#include <unistd.h>
#else
#error "PS4 runtime clock/thread provider only supports FreeBSD PS4 and Linux host test"
#endif

namespace nx::plat {

uint64_t monotonic_ns() {
    timespec now{};
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0 || now.tv_sec < 0 ||
        now.tv_nsec < 0 || now.tv_nsec >= 1000000000L) return 0;
    constexpr uint64_t kBillion = 1000000000ull;
    const auto sec = static_cast<uint64_t>(now.tv_sec);
    if (sec > (std::numeric_limits<uint64_t>::max() -
               static_cast<uint64_t>(now.tv_nsec)) / kBillion)
        return std::numeric_limits<uint64_t>::max();
    return sec * kBillion + static_cast<uint64_t>(now.tv_nsec);
}

void sleep_ns(int64_t ns) {
    if (ns <= 0) return;
    timespec remaining{};
    remaining.tv_sec = static_cast<time_t>(ns / 1000000000ll);
    remaining.tv_nsec = static_cast<long>(ns % 1000000000ll);
    while (nanosleep(&remaining, &remaining) == -1 && errno == EINTR) {
        // Respect interrupted sleeps without returning early.
    }
}

void yield() {
    (void)sched_yield();
}

int64_t current_thread_id() {
#if defined(__FreeBSD__)
    // PS4 libkernel native thread identifier, not an invented counter or
    // a cast of pthread_t (which is not necessarily an integer).
    return static_cast<int64_t>(scePthreadGetthreadid());
#else
    return static_cast<int64_t>(syscall(SYS_gettid));
#endif
}
} // namespace nx::plat
