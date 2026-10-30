// Lingshu207: independent 16-KiB flexible-memory diagnostic. NOT A GAME.
// This does not replace a previously reserved guest window or try huge maps.
// Host tests call this exact algorithm with simulated native function pointers.
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <limits>

namespace lingshu207 {
constexpr std::size_t kPage=0x4000;
constexpr std::int32_t kReadOnly=1;
constexpr std::int32_t kReadWrite=3;
using MapFn=std::int32_t(*)(void**,std::size_t,std::int32_t,std::int32_t);
using ProtectFn=std::int32_t(*)(const void*,std::size_t,std::int32_t);
using UnmapFn=std::int32_t(*)(void*,std::size_t);
struct Result {
    std::int32_t map_rc=0, read_protect_rc=0, restore_protect_rc=0, unmap_rc=0;
    std::uintptr_t returned=0;
    bool mapped=false, bytes_verified=false, readonly_verified=false;
    bool rw_restored=false, cleanup_attempted=false, cleanup_ok=false;
    bool unsafe=false, complete=false;
};

inline Result run(std::FILE* log,MapFn map_fn,ProtectFn protect_fn,
                  UnmapFn unmap_fn) {
    Result r{};
    if (!log || !map_fn || !protect_fn || !unmap_fn) return r;
    std::fprintf(log,"LINGSHU207_START=FLEXIBLE_MAP_16K_ONLY_NO_GUEST_RESERVE_NO_GAME\n");
    std::fprintf(log,"LINGSHU207_GUARD=ONLY_ONE_16K_NO_MAP_FIXED_CLEANUP_REQUIRED\n");
    std::fflush(log);
    void* mapped=nullptr; // Let the kernel choose a fresh user-space location.
    std::fprintf(log,"LINGSHU207_BEFORE=MAP_FLEXIBLE bytes=%llu prot=3 flags=0\n",
                 static_cast<unsigned long long>(kPage));
    std::fflush(log);
    r.map_rc=map_fn(&mapped,kPage,kReadWrite,0);
    r.returned=reinterpret_cast<std::uintptr_t>(mapped);
    if (r.map_rc!=0) {
        r.unsafe=(mapped!=nullptr); // Unknown mutation after an error: stop.
        std::fprintf(log,"LINGSHU207_MAP=status_%s rc=0x%08x returned=%llx\n",
                     r.unsafe?"ERROR_CHANGED_POINTER_UNSAFE":"DENIED",
                     static_cast<unsigned>(r.map_rc),
                     static_cast<unsigned long long>(r.returned));
        std::fflush(log);
        return r;
    }
    if(r.returned<0x10000 || r.returned%kPage!=0 ||
       r.returned>std::numeric_limits<std::uintptr_t>::max()-kPage) {
        r.unsafe=true;
        std::fprintf(log,"LINGSHU207_MAP=status_ANOMALOUS_POINTER_STOP returned=%llx\n",
                     static_cast<unsigned long long>(r.returned));
        std::fflush(log);
        return r; // Do not dereference or attempt to unmap a malformed pointer.
    }
    r.mapped=true;
    std::fprintf(log,"LINGSHU207_MAP=status_OK returned=%llx\n",
                 static_cast<unsigned long long>(r.returned));
    std::fflush(log);
    // Only after a successful map and strict pointer validation:
    auto* p=static_cast<volatile unsigned char*>(mapped);
    p[0]=0xA5;
    p[kPage-1]=0x5A;
    r.bytes_verified=(p[0]==0xA5 && p[kPage-1]==0x5A);
    std::fprintf(log,"LINGSHU207_IO=%s\n",r.bytes_verified?"FIRST_LAST_BYTE_OK":"VERIFY_FAILED");
    std::fflush(log);
    if(r.bytes_verified) {
        r.read_protect_rc=protect_fn(mapped,kPage,kReadOnly);
        if(r.read_protect_rc==0) {
            r.readonly_verified=(p[0]==0xA5 && p[kPage-1]==0x5A);
            std::fprintf(log,"LINGSHU207_READ_ONLY=%s\n",
                         r.readonly_verified?"PROTECT_AND_READ_OK":"READ_VERIFY_FAILED");
            std::fflush(log);
            r.restore_protect_rc=protect_fn(mapped,kPage,kReadWrite);
            r.rw_restored=(r.restore_protect_rc==0);
            std::fprintf(log,"LINGSHU207_RW_RESTORE=%s rc=0x%08x\n",
                         r.rw_restored?"OK":"FAILED",
                         static_cast<unsigned>(r.restore_protect_rc));
            std::fflush(log);
        } else {
            std::fprintf(log,"LINGSHU207_READ_ONLY=MPROTECT_FAILED rc=0x%08x\n",
                         static_cast<unsigned>(r.read_protect_rc));
            std::fflush(log);
        }
    }
    // Always attempt cleanup of the exactly returned valid mapping.
    r.cleanup_attempted=true;
    r.unmap_rc=unmap_fn(mapped,kPage);
    r.cleanup_ok=(r.unmap_rc==0);
    r.unsafe=!r.cleanup_ok;
    std::fprintf(log,"LINGSHU207_UNMAP=%s rc=0x%08x\n",
                 r.cleanup_ok?"OK":"FAILED_UNSAFE",
                 static_cast<unsigned>(r.unmap_rc));
    r.complete=r.bytes_verified && r.readonly_verified &&
               r.rw_restored && r.cleanup_ok;
    std::fprintf(log,"LINGSHU207_SUMMARY mapped=%u io=%u readonly=%u rw_restored=%u cleanup=%u unsafe=%u complete=%u\n",
                 unsigned(r.mapped),unsigned(r.bytes_verified),
                 unsigned(r.readonly_verified),unsigned(r.rw_restored),
                 unsigned(r.cleanup_ok),unsigned(r.unsafe),unsigned(r.complete));
    std::fprintf(log,"LINGSHU207_FINAL=%s\n",
                 r.complete?"FLEXIBLE_16K_RW_RO_RW_AND_CLEANUP_OK_NOT_GAME":
                 r.unsafe?"STOP_UNSAFE_NOT_GAME":"INCOMPLETE_CLEANED_NOT_GAME");
    std::fflush(log);
    return r;
}
} // namespace lingshu207
