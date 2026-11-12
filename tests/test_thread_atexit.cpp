#include <atomic>
#include <cassert>
#include <pthread.h>

extern "C" int __cxa_thread_atexit_impl(
    void (*func)(void*), void* obj, void* dso_handle);

namespace {
std::atomic<int> next_slot{0};
int destructor_order[2] = {0, 0};

void record_destructor(void* value) {
    const int slot = next_slot.fetch_add(1, std::memory_order_relaxed);
    assert(slot >= 0 && slot < 2);
    destructor_order[slot] = *static_cast<int*>(value);
}

void* worker(void*) {
    static int first = 1;
    static int second = 2;
    assert(__cxa_thread_atexit_impl(&record_destructor, &first, nullptr) == 0);
    assert(__cxa_thread_atexit_impl(&record_destructor, &second, nullptr) == 0);
    return nullptr;
}
} // namespace

int main() {
    pthread_t thread{};
    assert(pthread_create(&thread, nullptr, &worker, nullptr) == 0);
    assert(pthread_join(thread, nullptr) == 0);
    assert(next_slot.load(std::memory_order_relaxed) == 2);
    assert(destructor_order[0] == 2);
    assert(destructor_order[1] == 1);
    return 0;
}
