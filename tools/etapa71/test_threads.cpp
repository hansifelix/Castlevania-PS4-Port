#include <atomic>
#include <cassert>
#include <cstdio>
#include <unistd.h>
namespace nx::plat {
    using ThreadFn = void (*)(void*);
    void start_thread(ThreadFn, void*, size_t);
    [[noreturn]] void exit_thread();
    void yield();
}
struct Data { std::atomic<int> progress{0}; };
void work(void* p) {
    auto* d = static_cast<Data*>(p);
    d->progress.fetch_add(1, std::memory_order_release);
    nx::plat::yield();
    d->progress.fetch_add(1, std::memory_order_release);
    nx::plat::exit_thread();
}
int main() {
    Data d;
    nx::plat::start_thread(&work, &d, 1024*1024);
    for (int i=0; i<2000 && d.progress.load(std::memory_order_acquire)!=2; ++i) {
        usleep(1000);
    }
    assert(d.progress.load(std::memory_order_acquire)==2);
    puts("KAZUMA71 HOST: pthread start / yield / exit reais = PASSOU");
}
