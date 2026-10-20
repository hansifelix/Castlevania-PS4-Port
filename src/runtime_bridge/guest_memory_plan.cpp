#include "runtime_bridge/guest_memory_plan.hpp"
#include <algorithm>
#include <limits>

namespace castlevania_ps4 {

const char* plan_result_name(PlanResult result) {
    switch (result) {
        case PlanResult::ok: return "ok";
        case PlanResult::zero_size: return "zero_size";
        case PlanResult::invalid_page_size: return "invalid_page_size";
        case PlanResult::misaligned: return "misaligned";
        case PlanResult::address_overflow: return "address_overflow";
        case PlanResult::overlaps: return "overlaps";
    }
    return "unknown";
}

PlanResult GuestMemoryPlan::add(std::uint64_t address, std::uint64_t size) {
    if (page_size_ == 0 || (page_size_ & (page_size_ - 1)) != 0)
        return PlanResult::invalid_page_size;
    if (size == 0) return PlanResult::zero_size;
    if (address % page_size_ || size % page_size_) return PlanResult::misaligned;
    if (size > std::numeric_limits<std::uint64_t>::max() - address)
        return PlanResult::address_overflow;

    const GuestRegion requested{address, address + size};
    const auto it = std::lower_bound(regions_.begin(), regions_.end(), requested.begin,
                                    [](const GuestRegion& a, std::uint64_t b) {
                                        return a.begin < b;
                                    });
    if (it != regions_.end() && requested.end > it->begin) return PlanResult::overlaps;
    if (it != regions_.begin() && (it - 1)->end > requested.begin) return PlanResult::overlaps;
    regions_.insert(it, requested);
    return PlanResult::ok;
}

}  // namespace castlevania_ps4
