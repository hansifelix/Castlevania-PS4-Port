// Lingshu208 - inspect one guest reservation and one independent flexible map.
// NO MAP_FIXED, no writes or reads through returned pointers, no game code.
// Native query is observational; both test mappings are released before exit.
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <limits>

namespace lingshu208 {
constexpr std::size_t kPage=0x4000;
constexpr std::uintptr_t kGuest=0x0000004000000000ull;
using ReserveFn=std::int32_t(*)(void**,std::size_t,std::int32_t,std::size_t);
using MapFn=std::int32_t(*)(void**,std::size_t,std::int32_t,std::int32_t);
using UnmapFn=std::int32_t(*)(void*,std::size_t);
struct Result {
    unsigned reservations=0, maps=0, queries=0, query_ok=0;
    unsigned cleanup=0, cleanup_ok=0;
    bool reserved_exact=false, flexible_mapped=false;
    bool unsafe=false, complete=false;
};
inline bool address_valid(std::uintptr_t a) {
    return a>=0x10000 && a%kPage==0 &&
           a<=std::numeric_limits<std::uintptr_t>::max()-kPage;
}
template<class Info>
using QueryFn=std::int32_t(*)(const void*,std::int32_t,Info*,std::size_t);

template<class Info>
inline Result run(std::FILE* log,ReserveFn reserve_fn,MapFn map_fn,
                  QueryFn<Info> query_fn,UnmapFn unmap_fn) {
    Result r{};
    if(!log || !reserve_fn || !map_fn || !query_fn || !unmap_fn)return r;
    std::fprintf(log,"LINGSHU208_START=ONE_RESERVED_VA_ONE_SEPARATE_FLEXIBLE_MAP_NO_GAME\n");
    std::fprintf(log,"LINGSHU208_GUARDS=16K_ONLY_NO_FIXED_NO_DEREFERENCE_REVERSE_CLEANUP\n");
    std::fflush(log);
    void* reserved=reinterpret_cast<void*>(kGuest);
    void* flexible=nullptr;
    auto query=[&](const char* label,const void* addr) {
        Info info{};
        ++r.queries;
        std::fprintf(log,"LINGSHU208_QUERY_BEFORE name=%s addr=%llx\n",
                     label,(unsigned long long)(std::uintptr_t)addr);
        std::fflush(log);
        const std::int32_t rc=query_fn(addr,0,&info,sizeof info);
        if(rc==0) {
            ++r.query_ok;
            std::fprintf(log,
                "LINGSHU208_QUERY name=%s status=OK start=%llx end=%llx prot=%d mtype=%d flex=%u direct=%u committed=%u\n",
                label,(unsigned long long)(std::uintptr_t)info.start_addr,
                (unsigned long long)(std::uintptr_t)info.end_addr,
                int(info.prot),int(info.mtype),
                unsigned(info.isFlexibleMemory),unsigned(info.isDirectMemory),
                unsigned(info.isCommitted));
        } else {
            std::fprintf(log,"LINGSHU208_QUERY name=%s status=UNAVAILABLE rc=0x%08x\n",
                         label,static_cast<unsigned>(rc));
        }
        std::fflush(log);
    };
    std::fprintf(log,"LINGSHU208_BEFORE=RESERVE addr=%llx bytes=%llu\n",
                 (unsigned long long)kGuest,(unsigned long long)kPage);
    std::fflush(log);
    ++r.reservations;
    const std::int32_t reserve_rc=reserve_fn(&reserved,kPage,0,kPage);
    const auto reserve_addr=(std::uintptr_t)reserved;
    if(reserve_rc!=0) {
        // A changed pointer on error is not evidence that no mapping exists.
        r.unsafe=(reserve_addr!=kGuest);
        std::fprintf(log,"LINGSHU208_RESERVE status=%s rc=0x%08x returned=%llx\n",
                     r.unsafe?"ERROR_MUTATED_POINTER_UNSAFE":"DENIED",
                     unsigned(reserve_rc),(unsigned long long)reserve_addr);
    } else if(!address_valid(reserve_addr)) {
        r.unsafe=true;
        std::fprintf(log,"LINGSHU208_RESERVE status=ANOMALOUS_POINTER_UNSAFE returned=%llx\n",
                     (unsigned long long)reserve_addr);
    } else if(reserve_addr!=kGuest) {
        // A relocated reservation may be cleaned up, but do not run
        // any further probes until its cleanup result is known.
        std::fprintf(log,"LINGSHU208_RESERVE status=RELOCATED requested=%llx returned=%llx\n",
                     (unsigned long long)kGuest,(unsigned long long)reserve_addr);
        std::fflush(log);
        ++r.cleanup;
        const auto rc=unmap_fn(reserved,kPage);
        if(rc==0)++r.cleanup_ok; else r.unsafe=true;
        std::fprintf(log,"LINGSHU208_RELEASE name=RELOCATED status=%s rc=0x%08x\n",
                     rc==0?"OK":"FAILED_UNSAFE",unsigned(rc));
    } else {
        r.reserved_exact=true;
        std::fprintf(log,"LINGSHU208_RESERVE status=EXACT_HELD rc=0x00000000\n");
        std::fflush(log);
        query("GUEST_RESERVED",reserved);
        // Kernel-chosen flexible mapping is a SEPARATE location.
        std::fprintf(log,"LINGSHU208_BEFORE=MAP_FLEX bytes=%llu prot=3 flags=0\n",
                     (unsigned long long)kPage);
        std::fflush(log);
        ++r.maps;
        const auto map_rc=map_fn(&flexible,kPage,3,0);
        const auto flex_addr=(std::uintptr_t)flexible;
        if(map_rc!=0) {
            r.unsafe=(flexible!=nullptr);
            std::fprintf(log,"LINGSHU208_FLEX status=%s rc=0x%08x returned=%llx\n",
                         r.unsafe?"ERROR_MUTATED_POINTER_UNSAFE":"DENIED",
                         unsigned(map_rc),(unsigned long long)flex_addr);
        } else if(!address_valid(flex_addr) ||
                  (flex_addr<kGuest+kPage && flex_addr+kPage>kGuest)) {
            r.unsafe=true;
            std::fprintf(log,"LINGSHU208_FLEX status=ANOMALOUS_OR_OVERLAP_UNSAFE returned=%llx\n",
                         (unsigned long long)flex_addr);
        } else {
            r.flexible_mapped=true;
            std::fprintf(log,"LINGSHU208_FLEX status=MAPPED_SEPARATELY returned=%llx\n",
                         (unsigned long long)flex_addr);
            std::fflush(log);
            query("FLEXIBLE_MAPPED",flexible);
            ++r.cleanup;
            const auto rc=unmap_fn(flexible,kPage);
            if(rc==0)++r.cleanup_ok; else r.unsafe=true;
            std::fprintf(log,"LINGSHU208_RELEASE name=FLEXIBLE status=%s rc=0x%08x\n",
                         rc==0?"OK":"FAILED_UNSAFE",unsigned(rc));
        }
        std::fflush(log);
        ++r.cleanup;
        const auto rc=unmap_fn(reserved,kPage);
        if(rc==0)++r.cleanup_ok; else r.unsafe=true;
        std::fprintf(log,"LINGSHU208_RELEASE name=GUEST_RESERVED status=%s rc=0x%08x\n",
                     rc==0?"OK":"FAILED_UNSAFE",unsigned(rc));
    }
    r.complete=r.reserved_exact && r.flexible_mapped &&
               r.queries==2 && r.query_ok==2 &&
               r.cleanup==2 && r.cleanup_ok==2 && !r.unsafe;
    std::fprintf(log,
        "LINGSHU208_SUMMARY reserve=%u exact=%u flexible=%u queries=%u query_ok=%u cleanup=%u cleanup_ok=%u unsafe=%u complete=%u\n",
        r.reservations,unsigned(r.reserved_exact),unsigned(r.flexible_mapped),
        r.queries,r.query_ok,r.cleanup,r.cleanup_ok,
        unsigned(r.unsafe),unsigned(r.complete));
    std::fprintf(log,"LINGSHU208_FINAL=%s\n",
                 r.complete?"TWO_VM_TYPES_QUERIED_AND_RELEASED_NOT_ENGINE":
                 r.unsafe?"STOP_UNSAFE_NOT_ENGINE":"PARTIAL_CLEAN_NOT_ENGINE");
    std::fflush(log);
    return r;
}
} // namespace lingshu208
