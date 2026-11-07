#include "port_core/aot_text_bounds.hpp"

namespace kazuma_port_core {
const char* aot_bounds_status_name(AotBoundsStatus status) {
    switch (status) {
        case AotBoundsStatus::ok: return "ok";
        case AotBoundsStatus::unknown_module: return "unknown_module";
        case AotBoundsStatus::invalid_text_span: return "invalid_text_span";
        case AotBoundsStatus::empty_function_table: return "empty_function_table";
        case AotBoundsStatus::misaligned_function: return "misaligned_function";
        case AotBoundsStatus::duplicate_function: return "duplicate_function";
        case AotBoundsStatus::out_of_order_function: return "out_of_order_function";
        case AotBoundsStatus::outside_text_span: return "outside_text_span";
        case AotBoundsStatus::guest_address_mismatch: return "guest_address_mismatch";
    }
    return "unknown";
}

AotBoundsReport check_aot_text_bounds(
    const GuestModuleIndex& index,
    const std::string& module_name,
    std::uint64_t text_offset,
    std::uint64_t text_size,
    const std::vector<std::uint64_t>& offsets) {

    const auto module = index.by_name(module_name);
    if (!module) return {AotBoundsStatus::unknown_module, 0, 0};

    // Compare with subtraction to avoid arithmetic overflow in guest ranges.
    if ((text_offset % 4) != 0 || (text_size % 4) != 0 ||
        text_size == 0 || text_offset >= module->size ||
        text_size > module->size - text_offset)
        return {AotBoundsStatus::invalid_text_span, 0, 0};

    if (offsets.empty()) return {AotBoundsStatus::empty_function_table, 0, 0};

    const auto text_end = text_offset + text_size; // safe after validation
    std::uint64_t previous = 0;
    bool have_previous = false;

    for (std::size_t i = 0; i < offsets.size(); ++i) {
        const auto offset = offsets[i];
        if (offset % 4)
            return {AotBoundsStatus::misaligned_function, i, offset};
        if (have_previous && offset == previous)
            return {AotBoundsStatus::duplicate_function, i, offset};
        if (have_previous && offset < previous)
            return {AotBoundsStatus::out_of_order_function, i, offset};
        if (offset < text_offset || offset >= text_end)
            return {AotBoundsStatus::outside_text_span, i, offset};

        // The module index guarantees base + module->size does not overflow.
        const auto hit = index.resolve(module->base + offset);
        if (!hit || hit->module != module_name || hit->offset != offset)
            return {AotBoundsStatus::guest_address_mismatch, i, offset};

        previous = offset;
        have_previous = true;
    }
    return {AotBoundsStatus::ok, offsets.size(), 0};
}
} // namespace kazuma_port_core
