// Lingshu 206: five simultaneous fixed-address PS4 virtual reservations.
// Independent diagnostic, NEVER a game, no MAP_FIXED or page writes.
// Reserve each 16MiB window without releasing prior windows. Cleanup in reverse.
// This probe does not validate 4/6/64GiB ranges or physical memory commits.
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <limits>
namespace lingshu206 {
constexpr std::size_t kPS4Page = 0x4000;
constexpr std::size_t kBytes = 16u * 1024u * 1024u;
constexpr std::size_t kCount = 5;
struct Region { const char* name; std::uintptr_t address; };
constexpr Region kRegions[kCount] = {
    {"MODULES",0x0000004000000000ull},
    {"HEAP",   0x0000005000000000ull},
    {"ALIAS",  0x0000005800000000ull},
    {"STACK",  0x0000006800000000ull},
    {"KERNEL", 0x0000006a00000000ull}
};
static_assert(sizeof(std::uintptr_t)>=8, "requires a 64-bit address space");
static_assert(kBytes%kPS4Page==0);
using ReserveFn = std::int32_t(*)(void**,std::size_t,std::int32_t,std::size_t);
using ReleaseFn = std::int32_t(*)(void*,std::size_t);

struct Outcome {
    unsigned attempts=0, exact=0, denied=0, relocated=0;
    unsigned released=0, release_failed=0, unsafe=0;
    bool all_five_coexisted=false;
    bool fully_released=false;
    bool safe_to_continue=false;
};

inline Outcome run(std::FILE* log, ReserveFn reserve_fn, ReleaseFn release_fn) {
    Outcome result{};
    if (!log || !reserve_fn || !release_fn) return result;
    std::uintptr_t held[kCount]{};
    unsigned held_count=0;
    bool stop=false;
    std::fprintf(log,"LINGSHU206_START=FIVE_SIMULTANEOUS_16M_NO_GAME_NO_COMMIT\n");
    std::fflush(log);
    for (const Region& r : kRegions) {
        // Validate the range, even if upstream constants are ever edited.
        if (!r.address || r.address%kPS4Page ||
            r.address>std::numeric_limits<std::uintptr_t>::max()-kBytes) {
            result.unsafe++;
            std::fprintf(log,"LINGSHU206_RESULT name=%s status=INVALID_GUEST_RANGE\n",r.name);
            std::fflush(log);
            stop=true;
            break;
        }
        void* actual=reinterpret_cast<void*>(r.address);
        std::fprintf(log,"LINGSHU206_BEFORE name=%s addr=%llx bytes=%llu held=%u\n",
            r.name,static_cast<unsigned long long>(r.address),
            static_cast<unsigned long long>(kBytes),held_count);
        std::fflush(log);
        const std::int32_t rc=reserve_fn(&actual,kBytes,0,kPS4Page);
        result.attempts++;
        const auto got=reinterpret_cast<std::uintptr_t>(actual);
        if (rc!=0) {
            if (got!=r.address) {
                result.unsafe++;
                std::fprintf(log,"LINGSHU206_RESULT name=%s status=ERROR_CHANGED_PTR native_rc=0x%08x returned=%llx\n",
                    r.name,static_cast<unsigned>(rc),static_cast<unsigned long long>(got));
            } else {
                result.denied++;
                std::fprintf(log,"LINGSHU206_RESULT name=%s status=NATIVE_DENIED native_rc=0x%08x returned=%llx\n",
                    r.name,static_cast<unsigned>(rc),static_cast<unsigned long long>(got));
            }
            std::fflush(log);
            stop=true;
            break;
        }
        if (!got || got%kPS4Page ||
            got>std::numeric_limits<std::uintptr_t>::max()-kBytes) {
            // A successful syscall with a malformed output cannot be safely cleaned.
            result.unsafe++;
            std::fprintf(log,"LINGSHU206_RESULT name=%s status=ANOMALOUS_PTR returned=%llx\n",
                r.name,static_cast<unsigned long long>(got));
            std::fflush(log);
            stop=true;
            break;
        }
        if (got!=r.address) {
            result.relocated++;
            std::fprintf(log,"LINGSHU206_RESULT name=%s status=RELOCATED requested=%llx returned=%llx\n",
                r.name,static_cast<unsigned long long>(r.address),static_cast<unsigned long long>(got));
            std::fflush(log);
            // The unexpected address is not in held[]. Clean immediately.
            const std::int32_t release_rc=release_fn(actual,kBytes);
            std::fprintf(log,"LINGSHU206_RELEASE name=%s status=%s release_rc=0x%08x\n",
                r.name,release_rc==0?"OK_RELOCATED":"FAIL_RELOCATED",
                static_cast<unsigned>(release_rc));
            if(release_rc==0) result.released++;
            else {result.release_failed++;result.unsafe++;}
            std::fflush(log);
            stop=true;
            break;
        }
        held[held_count++]=got;
        result.exact++;
        std::fprintf(log,"LINGSHU206_RESULT name=%s status=EXACT_HELD native_rc=0x00000000 returned=%llx held=%u\n",
            r.name,static_cast<unsigned long long>(got),held_count);
        std::fflush(log);
    }
    result.all_five_coexisted=!stop && held_count==kCount;
    if (result.all_five_coexisted) {
        std::fprintf(log,"LINGSHU206_ALL_FIVE=COEXISTED_16M_EACH_NOT_GIANT_GUEST_RANGES\n");
        std::fflush(log);
    }
    // Always release every known exact reservation, in reverse order.
    for (unsigned i=held_count;i>0;--i) {
        const std::int32_t rc=release_fn(reinterpret_cast<void*>(held[i-1]),kBytes);
        std::fprintf(log,"LINGSHU206_RELEASE name=%s status=%s release_rc=0x%08x\n",
            kRegions[i-1].name,rc==0?"OK":"FAILED",static_cast<unsigned>(rc));
        if(rc==0)result.released++;
        else {result.release_failed++;result.unsafe++;}
        std::fflush(log);
    }
    result.fully_released=result.release_failed==0 && result.unsafe==0;
    result.safe_to_continue=result.fully_released;
    std::fprintf(log,
        "LINGSHU206_SUMMARY attempts=%u exact=%u denied=%u relocated=%u released=%u release_failed=%u unsafe=%u coexisted=%u safe=%u\n",
        result.attempts,result.exact,result.denied,result.relocated,
        result.released,result.release_failed,result.unsafe,
        unsigned(result.all_five_coexisted),unsigned(result.safe_to_continue));
    std::fprintf(log,"LINGSHU206_FINAL=%s\n",
        (result.all_five_coexisted && result.fully_released)?
        "FIVE_16M_SIMULTANEOUS_EXACT_AND_RELEASED_NOT_GAME":
        (result.safe_to_continue?"INCOMPLETE_BUT_CLEAN_NOT_GAME":
                                  "STOPPED_UNSAFE_NOT_GAME"));
    std::fflush(log);
    return result;
}
} // namespace lingshu206
