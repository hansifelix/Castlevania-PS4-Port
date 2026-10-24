// Exercício em Linux simulando a superfície da API; não valida PS4 real.
#include <orbis/libkernel.h>
#include <atomic>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <sys/syscall.h>
#include <unistd.h>
#include <sched.h>

extern "C" {
int scePthreadAttrInit(OrbisPthreadAttr* a) { return pthread_attr_init(a); }
int scePthreadAttrSetstacksize(OrbisPthreadAttr* a,size_t z) { return pthread_attr_setstacksize(a,z); }
int scePthreadAttrDestroy(OrbisPthreadAttr* a) { return pthread_attr_destroy(a); }
int scePthreadCreate(OrbisPthread* t,const OrbisPthreadAttr* a,void* (*f)(void*),void* ctx,const char*) { return pthread_create(t,a,f,ctx); }
int scePthreadDetach(OrbisPthread t) { return pthread_detach(t); }
void scePthreadExit(void* p) { pthread_exit(p); }
void scePthreadYield(void) { sched_yield(); }
int32_t scePthreadGetthreadid(void) { return (int32_t)syscall(SYS_gettid); }
OrbisPthread scePthreadSelf(void) { return pthread_self(); }
int scePthreadRename(OrbisPthread t,const char* name) { return pthread_setname_np(t,name); }
}
namespace nx::plat {
using ThreadFn=void (*)(void*);
void start_thread(ThreadFn,void*,size_t);
[[noreturn]] void exit_thread();
void yield();
int64_t current_thread_id();
void set_thread_name(const char*);
}
struct Data { std::atomic<int> phase{0}; std::atomic<int64_t> child_tid{0}; };
static void task(void* ptr) {
    auto& d=*static_cast<Data*>(ptr);
    nx::plat::set_thread_name("kazuma-worker");
    char label[16]{};
    assert(pthread_getname_np(pthread_self(),label,sizeof(label))==0);
    assert(strcmp(label,"kazuma-worker")==0);
    d.child_tid.store(nx::plat::current_thread_id());
    nx::plat::yield();
    d.phase.store(1);
    nx::plat::exit_thread();
}
int main() {
    Data d;
    const int64_t main_tid=nx::plat::current_thread_id();
    assert(main_tid>0);
    nx::plat::start_thread(&task,&d,1024*1024);
    for(int i=0;i<3000 && d.phase.load()==0;i++)usleep(1000);
    assert(d.phase.load()==1);
    assert(d.child_tid.load()>0 && d.child_tid.load()!=main_tid);
    puts("ETAPA72: API PS4 simulada no Linux — CRIAR/NOMEAR/ID/YIELD/SAIR OK");
}
