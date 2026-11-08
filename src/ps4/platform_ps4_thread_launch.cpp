// Kazuma Traducoes: actual PS4 native detached thread creation and exit.
// ABI matches pinned MIT runtime platform.h: nx::plat::start_thread.
// PS4 uses real scePthread* libkernel imports; Linux is a host-test only path.
// A failure stops the process rather than pretending a guest thread was created.
#include <platform.h>
#include <cstdlib>
#include <memory>
#include <new>
#include <pthread.h>
#include <unistd.h>

#if defined(KAZUMA_PS4)
#include <orbis/libkernel.h>
#elif !defined(__linux__)
#error "Thread launch provider requires explicit KAZUMA_PS4 or Linux test target"
#endif

namespace nx::plat {
namespace {
struct Start {
    ThreadFn fn;
    void* arg;
};

[[noreturn]] void fatal_thread_failure() {
    std::abort();
}
void* entry(void* raw) {
    std::unique_ptr<Start> ctx(static_cast<Start*>(raw));
    const ThreadFn fn = ctx->fn;
    void* const arg = ctx->arg;
    ctx.reset();
    fn(arg);
    return nullptr;
}
} // namespace

void start_thread(ThreadFn fn, void* arg, size_t stack_size) {
    if (!fn) fatal_thread_failure();

#if defined(KAZUMA_PS4)
    OrbisPthreadAttr attr{};
    if (scePthreadAttrInit(&attr) != 0) fatal_thread_failure();
    if (stack_size && scePthreadAttrSetstacksize(&attr, stack_size) != 0)
        fatal_thread_failure();
    if (scePthreadAttrSetdetachstate(&attr, ORBIS_PTHREAD_CREATE_DETACHED) != 0)
        fatal_thread_failure();
#else
    pthread_attr_t attr{};
    if (pthread_attr_init(&attr) != 0) fatal_thread_failure();
    if (stack_size && pthread_attr_setstacksize(&attr, stack_size) != 0)
        fatal_thread_failure();
    if (pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED) != 0)
        fatal_thread_failure();
#endif

    std::unique_ptr<Start> ctx(new (std::nothrow) Start{fn, arg});
    if (!ctx) fatal_thread_failure();

#if defined(KAZUMA_PS4)
    OrbisPthread thread{};
    const int result = scePthreadCreate(&thread, &attr, &entry, ctx.get(),
                                      "kazuma-guest");
    const int attr_result = scePthreadAttrDestroy(&attr);
#else
    pthread_t thread{};
    const int result = pthread_create(&thread, &attr, &entry, ctx.get());
    const int attr_result = pthread_attr_destroy(&attr);
#endif
    if (result != 0 || attr_result != 0) fatal_thread_failure();
    // Ownership belongs to the detached thread. entry() frees the context.
    ctx.release();
}

[[noreturn]] void exit_thread() {
#if defined(KAZUMA_PS4)
    scePthreadExit(nullptr);
#else
    pthread_exit(nullptr);
#endif
    std::abort(); // Defensive: pthread exit functions must not return.
}

[[noreturn]] void exit_process(int code) {
    // An immediate process exit never invokes guest destructors while multiple
    // detached emulated threads may still be using guest memory.
    _exit(code);
}
} // namespace nx::plat
