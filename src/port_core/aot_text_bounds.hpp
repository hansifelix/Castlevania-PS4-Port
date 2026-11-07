#pragma once
#include "port_core/guest_module_index.hpp"
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace kazuma_port_core {
// Validates AOT function addresses against a registered module's guest TEXT
// interval. All offsets are module-relative (as in nx::FuncEntry).
// Pure host-side contract: no game code or modules loaded.
enum class AotBoundsStatus {
    ok,
    unknown_module,
    invalid_text_span,
    empty_function_table,
    misaligned_function,
    duplicate_function,
    out_of_order_function,
    outside_text_span,
    guest_address_mismatch
};

const char* aot_bounds_status_name(AotBoundsStatus result);

struct AotBoundsReport {
    AotBoundsStatus status;
    std::size_t checked;
    std::uint64_t failed_offset;
};

AotBoundsReport check_aot_text_bounds(
    const GuestModuleIndex& index,
    const std::string& module_name,
    std::uint64_t text_offset,
    std::uint64_t text_size,
    const std::vector<std::uint64_t>& function_offsets);
} // namespace kazuma_port_core
