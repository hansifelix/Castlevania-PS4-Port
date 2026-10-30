#include "virtual_query_policy.h"
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
namespace {
struct QueryInfo {
    void* start_addr=nullptr;
    void* end_addr=nullptr;
    std::int64_t offset=0;
    std::int32_t prot=0,mtype=0;
    unsigned isFlexibleMemory:1;
    unsigned isDirectMemory:1;
    unsigned isStack:1;
    unsigned isPooledMemory:1;
    unsigned isCommitted:1;
    char name[32]{};
};
alignas(0x4000) unsigned char flexible_page[0x4000];
enum class Mode {Success,ReserveDenied,ReserveRelocated,QueryFailed,
                 MapDenied,MapNullSuccess,ReleaseFailed};
Mode mode=Mode::Success;
unsigned reserves=0,maps=0,queries=0,releases=0;
std::vector<std::uintptr_t> freed;
void reset(Mode m){mode=m;reserves=maps=queries=releases=0;freed.clear();}
std::int32_t reserve_mock(void** p,std::size_t n,std::int32_t flags,std::size_t align) {
    assert(p && (std::uintptr_t)*p==lingshu208::kGuest);
    assert(n==lingshu208::kPage && align==n && flags==0);
    ++reserves;
    if(mode==Mode::ReserveDenied)return -7;
    if(mode==Mode::ReserveRelocated)*p=reinterpret_cast<void*>(lingshu208::kGuest+n);
    return 0;
}
std::int32_t map_mock(void** p,std::size_t n,std::int32_t prot,std::int32_t flags) {
    assert(p && !*p && n==lingshu208::kPage && prot==3 && flags==0);
    ++maps;
    if(mode==Mode::MapDenied)return -8;
    if(mode==Mode::MapNullSuccess)return 0;
    *p=flexible_page;
    return 0;
}
std::int32_t query_mock(const void* p,std::int32_t flags,QueryInfo* info,std::size_t n) {
    assert(flags==0 && info && n==sizeof(QueryInfo));
    assert(p==reinterpret_cast<void*>(lingshu208::kGuest) ||
           p==static_cast<void*>(flexible_page));
    ++queries;
    if(mode==Mode::QueryFailed && queries==1)return -9;
    info->start_addr=const_cast<void*>(p);
    info->end_addr=reinterpret_cast<void*>((std::uintptr_t)p+lingshu208::kPage);
    const bool flexible=(p==flexible_page);
    info->prot=flexible?3:0;
    info->mtype=flexible?4:0;
    info->isFlexibleMemory=flexible?1u:0u;
    info->isDirectMemory=0;
    info->isCommitted=flexible?1u:0u;
    return 0;
}
std::int32_t unmap_mock(void* p,std::size_t n) {
    assert(n==lingshu208::kPage);
    const auto a=(std::uintptr_t)p;
    assert(a==lingshu208::kGuest || a==lingshu208::kGuest+n ||
           p==static_cast<void*>(flexible_page));
    ++releases;
    freed.push_back(a);
    if(mode==Mode::ReleaseFailed && releases==1)return -12;
    return 0;
}
struct Attempt {lingshu208::Result state;std::string log;};
Attempt perform(){
    std::FILE* f=std::tmpfile();
    assert(f);
    const auto state=lingshu208::run<QueryInfo>(
        f,reserve_mock,map_mock,query_mock,unmap_mock);
    assert(std::fflush(f)==0);
    std::rewind(f);
    std::string log;
    char b[1024];
    while(std::size_t n=std::fread(b,1,sizeof b,f))log.append(b,n);
    assert(std::fclose(f)==0);
    return {state,log};
}
}
int main(){
    reset(Mode::Success);
    auto ok=perform();
    assert(ok.state.complete && !ok.state.unsafe && ok.state.queries==2 && ok.state.query_ok==2);
    assert(reserves==1 && maps==1 && queries==2 && releases==2);
    assert(freed[0]==(std::uintptr_t)flexible_page && freed[1]==lingshu208::kGuest);
    assert(ok.log.find("LINGSHU208_QUERY name=GUEST_RESERVED status=OK")!=std::string::npos);
    assert(ok.log.find("LINGSHU208_QUERY name=FLEXIBLE_MAPPED status=OK")!=std::string::npos);
    assert(ok.log.find("LINGSHU208_FINAL=TWO_VM_TYPES_QUERIED_AND_RELEASED_NOT_ENGINE")!=std::string::npos);
    std::puts("LINGSHU208_TWO_QUERY_TYPES=PASS_HOST_MOCK");

    reset(Mode::ReserveDenied);
    auto denied=perform();
    assert(!denied.state.complete && !denied.state.unsafe && reserves==1 && maps==0 && releases==0);
    std::puts("LINGSHU208_RESERVE_DENIED=PASS_HOST_MOCK");

    reset(Mode::ReserveRelocated);
    auto relocated=perform();
    assert(!relocated.state.complete && !relocated.state.unsafe);
    assert(reserves==1 && maps==0 && releases==1 && freed[0]==lingshu208::kGuest+lingshu208::kPage);
    std::puts("LINGSHU208_RELOCATED_CLEANUP=PASS_HOST_MOCK");

    reset(Mode::QueryFailed);
    auto query=perform();
    assert(!query.state.complete && !query.state.unsafe && query.state.query_ok==1);
    assert(reserves==1 && maps==1 && releases==2);
    std::puts("LINGSHU208_QUERY_UNAVAILABLE_CLEANUP=PASS_HOST_MOCK");

    reset(Mode::MapDenied);
    auto map=perform();
    assert(!map.state.complete && !map.state.unsafe && map.state.cleanup_ok==1);
    assert(reserves==1 && maps==1 && releases==1 && freed[0]==lingshu208::kGuest);
    std::puts("LINGSHU208_FLEX_MAP_DENIED_CLEANUP=PASS_HOST_MOCK");

    reset(Mode::MapNullSuccess);
    auto nullmap=perform();
    assert(!nullmap.state.complete && nullmap.state.unsafe && maps==1 && releases==1);
    std::puts("LINGSHU208_FLEX_MAP_NULL_STOP=PASS_HOST_MOCK");

    reset(Mode::ReleaseFailed);
    auto cleanup=perform();
    assert(!cleanup.state.complete && cleanup.state.unsafe && cleanup.state.cleanup_ok==1);
    assert(releases==2 && freed[0]==(std::uintptr_t)flexible_page &&
           freed[1]==lingshu208::kGuest);
    std::puts("LINGSHU208_RELEASE_ERROR_QUARANTINE=PASS_HOST_MOCK");
    std::puts("LINGSHU208_HOST_SUITE=PASS_NOT_PS4");
}
