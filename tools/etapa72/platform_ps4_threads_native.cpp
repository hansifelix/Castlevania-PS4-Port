// Kazuma 72 — 5 funções reais do contrato nx::plat de threads.
// No PS4 usa o libkernel/scePthread (não os símbolos POSIX pthread_create).
// MOCK PS4 é usado APENAS nos testes em Linux; não é um teste no console.
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <limits>
#include <new>

#if defined(__FreeBSD__) || defined(KAZUMA_MOCK_PS4)
#include <orbis/libkernel.h>
#else
#include <pthread.h>
#include <sched.h>
#include <unistd.h>
#endif

namespace nx::plat {
using ThreadFn = void (*)(void*);

namespace {
struct StartContext { ThreadFn fn; void* arg; };

void* entry(void* opaque) {
    auto* context = static_cast<StartContext*>(opaque);
    ThreadFn fn = context->fn;
    void* arg = context->arg;
    delete context;
    fn(arg);
    return nullptr;
}

// Pedido de stack não é descartado silenciosamente; não usar alinhamento
// arbitrário em nome do kernel. 16 KiB é granularidade de endereços usada
// pelo PS4; libc valida a stack pedida na chamada abaixo.
size_t rounded_stack(size_t requested, size_t unit) {
    if (requested == 0) return 0;
    if (requested > std::numeric_limits<size_t>::max() - (unit - 1))
        std::abort();
    return ((requested + unit - 1) / unit) * unit;
}
}

void start_thread(ThreadFn fn, void* arg, size_t stack_size) {
    if (!fn) std::abort();
    auto* context = new (std::nothrow) StartContext{fn, arg};
    if (!context) std::abort();
#if defined(__FreeBSD__) || defined(KAZUMA_MOCK_PS4)
    OrbisPthreadAttr attr{};
    if (scePthreadAttrInit(&attr) != 0) std::abort();
    if (stack_size != 0) {
        // Reserva mínima conservadora, sem afirmar que substitui validação
        // no PS4. stack_size >= 64KiB é a política deste experimento.
        const size_t size = rounded_stack(stack_size < 65536 ? 65536 : stack_size, 16384);
        if (scePthreadAttrSetstacksize(&attr, size) != 0) std::abort();
    }
    OrbisPthread thread{};
    const int created = scePthreadCreate(&thread, &attr, entry, context, "kazuma-runtime");
    if (scePthreadAttrDestroy(&attr) != 0) std::abort();
    if (created != 0) { delete context; std::abort(); }
    if (scePthreadDetach(thread) != 0) std::abort();
#else
    pthread_attr_t attr{};
    if (pthread_attr_init(&attr) != 0) std::abort();
    if (stack_size != 0) {
        const size_t size = rounded_stack(stack_size < PTHREAD_STACK_MIN ? PTHREAD_STACK_MIN : stack_size, 4096);
        if (pthread_attr_setstacksize(&attr, size) != 0) std::abort();
    }
    if (pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED) != 0) std::abort();
    pthread_t thread{};
    const int created = pthread_create(&thread, &attr, entry, context);
    pthread_attr_destroy(&attr);
    if (created != 0) { delete context; std::abort(); }
#endif
}

[[noreturn]] void exit_thread() {
#if defined(__FreeBSD__) || defined(KAZUMA_MOCK_PS4)
    scePthreadExit(nullptr);
#else
    pthread_exit(nullptr);
#endif
    __builtin_unreachable();
}

void yield() {
#if defined(__FreeBSD__) || defined(KAZUMA_MOCK_PS4)
    scePthreadYield();
#else
    sched_yield();
#endif
}

int64_t current_thread_id() {
#if defined(__FreeBSD__) || defined(KAZUMA_MOCK_PS4)
    return static_cast<int64_t>(scePthreadGetthreadid());
#else
    // Identificador POSIX suficiente para teste de unicidade em Linux.
    // Não é exposto como identificador de thread de kernel Linux.
    pthread_t t = pthread_self();
    static_assert(sizeof(t) <= sizeof(uint64_t));
    uint64_t value = 0;
    __builtin_memcpy(&value, &t, sizeof(t));
    return static_cast<int64_t>(value);
#endif
}

void set_thread_name(const char* name) {
    if (!name || !*name) return;
#if defined(__FreeBSD__) || defined(KAZUMA_MOCK_PS4)
    // Não reivindicamos sucesso se a API do libkernel devolver erro.
    if (scePthreadRename(scePthreadSelf(), name) != 0) std::abort();
#else
    // pthread Linux limita nome; nome maior é reduzido explicitamente.
    char n[16]{};
    size_t i = 0;
    while (name[i] && i < 15) { n[i] = name[i]; ++i; }
    if (pthread_setname_np(pthread_self(), n) != 0) std::abort();
#endif
}
} // namespace nx::plat
