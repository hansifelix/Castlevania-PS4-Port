// Lingshu 187: conservative PS4 virtual-address reservation probe.
// Host-testable C++20 logic. No game data, MAP_FIXED, dereferencing or
// changes to the existing nx::plat::reserve implementation.
#pragma once
#include <cstddef>
#include <cstdint>
#include <limits>

namespace lingshu187 {
constexpr std::size_t kPS4Page = 0x4000; // Measured in user's stage-181 log.
constexpr std::size_t kMaxTrial = 16u * 1024u * 1024u;
using ReserveFn = std::int32_t (*)(void**, std::size_t, std::int32_t, std::size_t);
using ReleaseFn = std::int32_t (*)(void*, std::size_t);

enum class Status {
    InvalidInput,
    NativeReserveFailed,
    ErrorChangedAddress,
    SuccessNullPointer,
    AnomalousReturnedAddress,
    ExactAddressReleased,
    RelocatedAddressReleased,
    CleanupFailed
};
struct Result {
    Status status=Status::InvalidInput;
    std::uintptr_t requested=0;
    std::uintptr_t returned=0;
    std::size_t size=0;
    std::int32_t reserve_rc=0;
    std::int32_t release_rc=0;
    bool attempted=false;
    bool release_attempted=false;
    bool safe_to_continue=false;
};

inline bool input_ok(std::uintptr_t addr, std::size_t bytes) {
    if (!addr || (addr % kPS4Page) != 0 ||
        !bytes || (bytes % kPS4Page) != 0 || bytes > kMaxTrial)
        return false;
    return addr <= std::numeric_limits<std::uintptr_t>::max() - bytes;
}

inline Result probe(std::uintptr_t requested, std::size_t bytes,
                    ReserveFn reserve_fn, ReleaseFn release_fn) {
    Result out{};
    out.requested=requested;
    out.size=bytes;
    if (!reserve_fn || !release_fn || !input_ok(requested,bytes)) return out;
    void* actual=reinterpret_cast<void*>(requested);
    out.attempted=true;
    // 0 is used in public Orbis samples, but this code must be validated
    // on the owner's firmware before any engine integration.
    out.reserve_rc=reserve_fn(&actual,bytes,0,kPS4Page);
    out.returned=reinterpret_cast<std::uintptr_t>(actual);
    if (out.reserve_rc!=0) {
        // A failed native call must not silently change the output pointer.
        // If it does, we cannot guarantee whether the OS reserved anything.
        out.status=out.returned==requested ? Status::NativeReserveFailed
                                          : Status::ErrorChangedAddress;
        out.safe_to_continue=(out.returned==requested);
        return out;
    }
    if (!actual) {
        out.status=Status::SuccessNullPointer;
        return out; // anomalous result; stop trials; no address to release
    }
    const bool aligned = (out.returned % kPS4Page) == 0;
    const bool in_range = out.returned <=
        std::numeric_limits<std::uintptr_t>::max() - bytes;
    out.release_attempted=true;
    // Always attempt cleanup of a successful reservation at the address
    // actually returned. Never dereference the pointer or call MAP_FIXED.
    out.release_rc=release_fn(actual,bytes);
    if (out.release_rc!=0) {
        out.status=Status::CleanupFailed;
        return out; // stop further trials, do not risk accumulating ranges
    }
    if (!aligned || !in_range) {
        // The native call reported success but returned a pointer that cannot
        // represent an aligned range. Even if cleanup returned success, STOP:
        // no confidence in the reserve/release contract on this firmware.
        out.status=Status::AnomalousReturnedAddress;
        out.safe_to_continue=false;
        return out;
    }
    out.status=out.returned==requested ? Status::ExactAddressReleased
                                     : Status::RelocatedAddressReleased;
    out.safe_to_continue=true;
    return out;
}

inline const char* label(Status s) {
    switch (s) {
       case Status::InvalidInput:return "INVALID_INPUT";
       case Status::NativeReserveFailed:return "NATIVE_RESERVE_FAILED";
       case Status::ErrorChangedAddress:return "ERROR_CHANGED_POINTER_STOP";
       case Status::SuccessNullPointer:return "ANOMALOUS_NULL";
       case Status::AnomalousReturnedAddress:return "ANOMALOUS_RETURNED_ADDRESS_STOP";
       case Status::ExactAddressReleased:return "EXACT_RELEASED";
       case Status::RelocatedAddressReleased:return "RELOCATED_RELEASED";
       case Status::CleanupFailed:return "CLEANUP_FAILED_STOP";
    }
    return "UNEXPECTED";
}
}
