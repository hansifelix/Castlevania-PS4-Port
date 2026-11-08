#include <platform.h>
#include <cassert>
#include <cstdint>
#include <limits>
#include <thread>
#include <atomic>

int main() {
    using namespace nx::plat;
    const auto t0 = monotonic_ns();
    assert(t0 > 0);
    sleep_ns(-1); // invalid delay is not converted to an infinite unsigned sleep
    sleep_ns(0);
    yield();
    const auto id = current_thread_id();
    assert(id > 0);
    std::atomic<int64_t> child_id{0};
    std::thread child([&] {
        child_id.store(current_thread_id());
        assert(monotonic_ns() > 0);
        yield();
    });
    child.join();
    assert(child_id.load() > 0);
    assert(child_id.load() != id); // Native OS thread IDs are distinct for live threads.
    sleep_ns(2500000); // 2.5 milliseconds, an actual POSIX nanosleep
    const auto t1 = monotonic_ns();
    assert(t1 >= t0);
    assert(t1 - t0 >= 1000000); // allow scheduler jitter and coarse clocks
    assert(t1 != std::numeric_limits<uint64_t>::max());
}
