// Stage 187 - PS4 SDK bridge for a separate homebrew diagnostic ONLY.
// DO NOT link into the game or call from nx::boot until console validation.
#include "native_reserve_policy.h"
#include <orbis/libkernel.h>
#include <cstdint>
#include <cstdio>

extern "C" bool lingshu187_native_probe(std::FILE* log) {
    if (!log) return false;
    constexpr struct Region { const char* name; std::uintptr_t addr; } regions[] = {
        {"MODULES",0x0000004000000000ull},
        {"HEAP",0x0000005000000000ull},
        {"ALIAS",0x0000005800000000ull},
        {"STACK",0x0000006800000000ull},
        {"KERNEL",0x0000006a00000000ull},
        {"THUNK",0x0000006f00000000ull}
    };
    constexpr std::size_t sizes[]={lingshu187::kPS4Page,1024u*1024u,
                                   lingshu187::kMaxTrial};
    // Distinguish successfully executing the *diagnostic* from successful
    // exact-address reservation. The prior bool alone hid this difference.
    unsigned attempts=0, exact=0, relocated=0, denied=0, unsafe=0;
    std::fprintf(log,"LINGSHU187_NATIVE_START=SMALL_VA_ONLY_NO_GAME\n");
    std::fflush(log);
    for (const auto& r : regions) {
        for (auto size : sizes) {
            // Flush BEFORE attempting any syscalls, so a crash records which
            // test was in progress; no large memory requests or data writes.
            std::fprintf(log,"LINGSHU187_BEFORE name=%s addr=%llx bytes=%llu\n",
                r.name,(unsigned long long)r.addr,(unsigned long long)size);
            std::fflush(log);
            const auto result=lingshu187::probe(r.addr,size,
                sceKernelReserveVirtualRange,sceKernelMunmap);
            ++attempts;
            switch (result.status) {
                case lingshu187::Status::ExactAddressReleased: ++exact; break;
                case lingshu187::Status::RelocatedAddressReleased: ++relocated; break;
                case lingshu187::Status::NativeReserveFailed: ++denied; break;
                default: ++unsafe; break;
            }
            std::fprintf(log,"LINGSHU187_RESULT name=%s status=%s native_rc=0x%08x release_rc=0x%08x requested=%llx returned=%llx bytes=%llu\n",
                r.name,lingshu187::label(result.status),
                static_cast<unsigned>(result.reserve_rc),
                static_cast<unsigned>(result.release_rc),
                (unsigned long long)result.requested,
                (unsigned long long)result.returned,
                (unsigned long long)result.size);
            std::fflush(log);
            if (!result.safe_to_continue) {
                std::fprintf(log,"LINGSHU188_SUMMARY attempts=%u exact=%u relocated=%u native_failed=%u unsafe=%u stopped=1\n",
                    attempts,exact,relocated,denied,unsafe);
                std::fprintf(log,"LINGSHU187_ABORT=UNSAFE_AFTER_NATIVE_RESPONSE\n");
                std::fflush(log);
                return false;
            }
            if (result.status==lingshu187::Status::NativeReserveFailed ||
                result.status==lingshu187::Status::RelocatedAddressReleased)
                break; // Don't increase size after unsuccessful exact reserve.
        }
    }
    std::fprintf(log,"LINGSHU188_SUMMARY attempts=%u exact=%u relocated=%u native_failed=%u unsafe=%u stopped=0\n",
        attempts,exact,relocated,denied,unsafe);
    std::fprintf(log,"LINGSHU188_DIAGNOSTIC_OUTCOME=%s\n",
        exact ? "EXACT_SMALL_RESERVATION_OBSERVED_NOT_GAME_BOOT" :
                "NO_EXACT_SMALL_RESERVATIONS_NOT_GAME_BOOT");
    std::fprintf(log,"LINGSHU187_FINISHED=SMALL_PROBES_ONLY_NOT_ENGINE_BOOT\n");
    std::fflush(log);
    return true;
}
