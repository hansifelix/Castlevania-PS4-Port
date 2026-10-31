// Etapa 178: static real guest-address layout check BEFORE calling nx::boot().
// Validates the exact upstream nx::memory_init() reservation geometry for AOT
// modules, heap, alias, stack, kernel and thunk. No actual PS4 mmap is attempted.
// Hardware mappings can still fail despite passing this structural preflight.
#include <nx/runtime.h>
#include "platform.h"

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>

namespace {
struct Span { uint64_t address, size; const char* name; };

bool failed(const char* message) {
    nx::plat::log_line(message);
    return false;
}

bool fits(const Span& span, uint64_t guest_end) {
    // Avoid integer overflow and accept only nonempty 16-KiB-aligned spans.
    return span.size && (span.address & 0x3FFFu) == 0 &&
           (span.size & 0x3FFFu) == 0 &&
           span.address >= nx::kAddressSpaceBase &&
           span.address < guest_end &&
           span.size <= guest_end - span.address;
}

bool overlaps(const Span& left, const Span& right) {
    return left.address < right.address + right.size &&
           right.address < left.address + left.size;
}
} // namespace

extern "C" bool lingshu_ps4_guest_layout_valid() {
    const auto mods = nx::linked_modules();
    if (mods.size() != 3)
        return failed("LINGSHU178: expected three AOT modules in guest layout");

    constexpr const char* expected[3] = {"main", "sdk", "subsdk0"};
    uint64_t end_of_modules = nx::kModuleBase;
    uint64_t previous_end = nx::kModuleBase;
    constexpr uint64_t page = 0x4000;
    constexpr uint64_t guest_end = nx::kAddressSpaceBase + nx::kAddressSpaceSize;
    static_assert(nx::kAddressSpaceBase < guest_end);

    for (size_t i = 0; i < mods.size(); ++i) {
        const nx::ModuleInfo* mod = mods[i];
        if (!mod || !mod->name || std::strcmp(mod->name, expected[i]) != 0)
            return failed("LINGSHU178: unexpected AOT module in memory layout");
        if (mod->base < nx::kModuleBase || mod->base >= guest_end ||
            mod->base > std::numeric_limits<uint64_t>::max() - mod->bss ||
            mod->base + mod->bss > std::numeric_limits<uint64_t>::max() - mod->bss_size)
            return failed("LINGSHU178: module address arithmetic overflow / outside guest space");

        const uint64_t end = mod->base + mod->bss + mod->bss_size;
        if (end < mod->base || end > guest_end)
            return failed("LINGSHU178: module extends beyond guest address space");
        if (mod->base < previous_end)
            return failed("LINGSHU178: AOT module reservations overlap or have invalid order");
        previous_end = end;
        if (end > end_of_modules) end_of_modules = end;
    }
    const uint64_t used = end_of_modules - nx::kModuleBase;
    if (used == 0 || used > UINT64_MAX - (page - 1))
        return failed("LINGSHU178: invalid module reservation length");
    const uint64_t rounded = (used + page - 1) & ~(page - 1);

    const std::array<Span, 6> spans{{
        {nx::kModuleBase, rounded, "modules"},
        {nx::kHeapBase, nx::kHeapMax, "heap"},
        {nx::kAliasBase, nx::kAliasSize, "alias"},
        {nx::kStackBase, nx::kStackSize, "stack"},
        {nx::kKernelBase, nx::kKernelSize, "kernel"},
        {nx::kThunkBase, nx::kThunkSize, "thunk"}
    }};
    for (size_t i = 0; i < spans.size(); ++i) {
        if (!fits(spans[i], guest_end)) {
            char msg[180];
            std::snprintf(msg, sizeof(msg), "LINGSHU178: invalid guest region geometry: %s", spans[i].name);
            return failed(msg);
        }
        for (size_t j = i + 1; j < spans.size(); ++j)
            if (overlaps(spans[i], spans[j])) {
                char msg[180];
                std::snprintf(msg, sizeof(msg),
                              "LINGSHU178: guest regions overlap: %s and %s",
                              spans[i].name, spans[j].name);
                return failed(msg);
            }
    }
    nx::plat::log_line(
        "LINGSHU178: AOT guest layout geometry valid; PS4 hardware reservations STILL UNVERIFIED");
    return true;
}
