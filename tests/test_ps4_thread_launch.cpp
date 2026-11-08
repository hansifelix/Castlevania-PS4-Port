// Host-only POSIX behavior verification for actual PS4 thread provider source.
#include <platform.h>
#include <atomic>
#include <cassert>
#include <cstdint>
#include <chrono>
#include <thread>
#include <pthread.h>

struct Job {
    std::atomic<int> done{0};
    std::atomic<int64_t> tid{0};
    std::atomic<size_t> observed_stack{0};
};
static void run(void* raw) {
    auto* j = static_cast<Job*>(raw);
    j->tid.store(nx::plat::current_thread_id(), std::memory_order_relaxed);
#if defined(__linux__)
    pthread_attr_t attr{};
    if (pthread_getattr_np(pthread_self(), &attr) == 0) {
        size_t stack = 0;
        if (pthread_attr_getstacksize(&attr, &stack) == 0)
            j->observed_stack.store(stack, std::memory_order_relaxed);
        pthread_attr_destroy(&attr);
    }
#endif
    j->done.store(1, std::memory_order_release);
}
static void exit_early(void* raw) {
    auto* j = static_cast<Job*>(raw);
    j->done.store(1, std::memory_order_release);
    nx::plat::exit_thread();
}
static bool await(const Job& job) {
    for(int i=0; i<300; ++i) {
        if(job.done.load(std::memory_order_acquire)) return true;
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    return false;
}
int main() {
    using namespace nx::plat;
    Job first{}, second{}, early{};
    constexpr size_t kStack = 4u * 1024u * 1024u;
    const auto parent_id = current_thread_id();
    start_thread(run, &first, kStack);
    start_thread(run, &second, 0);
    start_thread(exit_early, &early, kStack);
    assert(await(first) && await(second) && await(early));
    assert(first.tid.load() > 0 && second.tid.load() > 0);
    assert(first.tid.load() != parent_id && second.tid.load() != parent_id);
    assert(first.observed_stack.load() >= kStack);
    // The detached context must remain usable after start_thread returns.
    const auto before = monotonic_ns();
    sleep_ns(1500000);
    assert(monotonic_ns() >= before);
}
