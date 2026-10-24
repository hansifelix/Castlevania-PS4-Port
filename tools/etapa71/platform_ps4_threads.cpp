// Kazuma 71: adaptação REAL e pequena do contrato nx::plat de threads.
// Compilada para PS4 com OpenOrbis; exercitada separadamente em Linux no CI.
// Não contém módulos, arquivos ou recursos de Castlevania.
#include <pthread.h>
#include <sched.h>
#include <unistd.h>
#include <cerrno>
#include <cstddef>
#include <cstdlib>
#include <limits>
#include <new>

namespace nx::plat {
using ThreadFn = void (*)(void*);

struct StartContext {
    ThreadFn fn;
    void* arg;
};

static void* thread_entry(void* opaque) {
    auto* ctx = static_cast<StartContext*>(opaque);
    ThreadFn fn = ctx->fn;
    void* arg = ctx->arg;
    delete ctx;
    fn(arg);
    return nullptr;
}

void start_thread(ThreadFn fn, void* arg, size_t stack_size) {
    // Sem 'sucesso' falso: a API upstream é void; falhas críticas encerram o
    // processo de teste em vez de executar sem as threads necessárias.
    if (!fn) std::abort();
    pthread_attr_t attr;
    if (pthread_attr_init(&attr) != 0) std::abort();
    if (pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED) != 0) std::abort();
    if (stack_size != 0) {
        long raw_page = sysconf(_SC_PAGESIZE);
        if (raw_page <= 0) std::abort();
        size_t page = static_cast<size_t>(raw_page);
        size_t min_stack = static_cast<size_t>(PTHREAD_STACK_MIN);
        if (stack_size < min_stack) stack_size = min_stack;
        if (stack_size > std::numeric_limits<size_t>::max() - (page - 1)) std::abort();
        size_t rounded = (stack_size + page - 1) / page * page;
        if (pthread_attr_setstacksize(&attr, rounded) != 0) std::abort();
    }
    auto* ctx = new (std::nothrow) StartContext{fn, arg};
    if (!ctx) std::abort();
    pthread_t thread;
    int result = pthread_create(&thread, &attr, thread_entry, ctx);
    pthread_attr_destroy(&attr);
    if (result != 0) {
        delete ctx;
        std::abort();
    }
}

[[noreturn]] void exit_thread() {
    pthread_exit(nullptr);
    __builtin_unreachable();
}

void yield() { sched_yield(); }
}  // namespace nx::plat
