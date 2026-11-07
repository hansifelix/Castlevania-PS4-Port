#include "port_core/guest_module_index.hpp"
#include <algorithm>

namespace kazuma_port_core {
namespace {
AddModuleResult from_plan(castlevania_ps4::PlanResult result) {
    using P = castlevania_ps4::PlanResult;
    switch (result) {
        case P::ok: return AddModuleResult::ok;
        case P::zero_size: return AddModuleResult::zero_size;
        case P::invalid_page_size: return AddModuleResult::invalid_page_size;
        case P::misaligned: return AddModuleResult::misaligned;
        case P::address_overflow: return AddModuleResult::address_overflow;
        case P::overlaps: return AddModuleResult::overlaps;
    }
    return AddModuleResult::overlaps; // fail closed on unknown planner result
}
}  // namespace

const char* add_module_result_name(AddModuleResult result) {
    switch (result) {
        case AddModuleResult::ok: return "ok";
        case AddModuleResult::empty_name: return "empty_name";
        case AddModuleResult::duplicate_name: return "duplicate_name";
        case AddModuleResult::zero_size: return "zero_size";
        case AddModuleResult::invalid_page_size: return "invalid_page_size";
        case AddModuleResult::misaligned: return "misaligned";
        case AddModuleResult::address_overflow: return "address_overflow";
        case AddModuleResult::overlaps: return "overlaps";
    }
    return "unknown";
}

GuestModuleIndex::GuestModuleIndex(std::uint64_t page_size) : plan_(page_size) {}

AddModuleResult GuestModuleIndex::add(const std::string& name,
                                       std::uint64_t base, std::uint64_t size) {
    if (name.empty()) return AddModuleResult::empty_name;
    if (by_name(name).has_value()) return AddModuleResult::duplicate_name;

    const auto status = from_plan(plan_.add(base, size));
    if (status != AddModuleResult::ok) return status;

    auto pos = std::lower_bound(modules_.begin(), modules_.end(), base,
        [](const GuestModule& module, std::uint64_t address) {
            return module.base < address;
        });
    modules_.insert(pos, GuestModule{name, base, size});
    return AddModuleResult::ok;
}

std::optional<GuestModule> GuestModuleIndex::by_name(const std::string& name) const {
    auto found = std::find_if(modules_.begin(), modules_.end(),
        [&name](const GuestModule& module) { return module.name == name; });
    if (found == modules_.end()) return std::nullopt;
    return *found;
}

std::optional<ResolvedAddress> GuestModuleIndex::resolve(
    std::uint64_t guest_address) const {
    const auto next = std::upper_bound(modules_.begin(), modules_.end(), guest_address,
        [](std::uint64_t addr, const GuestModule& module) {
            return addr < module.base;
        });
    if (next == modules_.begin()) return std::nullopt;
    const auto& module = *(next - 1);
    // Subtraction is safe: module.base <= guest_address due to upper_bound.
    if (guest_address - module.base >= module.size) return std::nullopt;
    return ResolvedAddress{module.name, guest_address - module.base};
}

}  // namespace kazuma_port_core
