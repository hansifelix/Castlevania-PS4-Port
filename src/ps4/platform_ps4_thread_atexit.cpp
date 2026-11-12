// SPDX-License-Identifier: MIT
// Adapted from orbis-ports/orbis-compat's src/orbis_thread_atexit.c
// (MIT, same maintainer; commit 6922a7b6f4291a28edd239f1a4db50ed7aa00359).
//
// libc++ forwards __cxa_thread_atexit to this C-library hook. OpenOrbis libc
// does not provide it, so register destructors with the real pthread TSD API.
// Destructors run on the registering worker thread in reverse registration
// order. Documented limitation: the initial process thread does not run POSIX
// key destructors when main returns / exit is called; dso_handle is ignored
// because this port statically links one title image and does not dlclose it.
#include <pthread.h>
#include <stdlib.h>

struct KazumaThreadDtor {
    void (*func)(void*);
    void* obj;
    KazumaThreadDtor* next;
};

static pthread_key_t g_thread_dtor_key;
static pthread_once_t g_thread_dtor_once = PTHREAD_ONCE_INIT;

static void kazuma_thread_dtor_run(void* head) {
    KazumaThreadDtor* d = static_cast<KazumaThreadDtor*>(head);
    while (d) {
        KazumaThreadDtor* next = d->next;
        d->func(d->obj);
        free(d);
        d = next;
    }
}

static void kazuma_thread_dtor_init() {
    (void)pthread_key_create(&g_thread_dtor_key, kazuma_thread_dtor_run);
}

extern "C" int __cxa_thread_atexit_impl(
    void (*func)(void*), void* obj, void* dso_handle) {
    (void)dso_handle;
    if (!func) return -1;
    if (pthread_once(&g_thread_dtor_once, kazuma_thread_dtor_init) != 0)
        return -1;

    auto* d = static_cast<KazumaThreadDtor*>(malloc(sizeof(*d)));
    if (!d) return -1;

    d->func = func;
    d->obj = obj;
    d->next = static_cast<KazumaThreadDtor*>(
        pthread_getspecific(g_thread_dtor_key));

    if (pthread_setspecific(g_thread_dtor_key, d) != 0) {
        free(d);
        return -1;
    }
    return 0;
}
