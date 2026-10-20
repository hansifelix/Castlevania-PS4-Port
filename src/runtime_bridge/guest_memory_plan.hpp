#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

// Kazuma Port Games: pure planning / validation, no allocation or PS4 API.
// Addresses use half-open intervals [begin, end) and a caller-chosen page size.
namespace castlevania_ps4 {

struct GuestRegion {
    std::uint64_t begin;
    std::uint64_t end;
};

enum class PlanResult {
    ok,
    zero_size,
    invalid_page_size,
    misaligned,
    address_overflow,
    overlaps,
};

const char* plan_result_name(PlanResult result);

class GuestMemoryPlan {
public:
    explicit GuestMemoryPlan(std::uint64_t page_size) : page_size_(page_size) {}

    // This does NOT reserve host memory; it only builds a validated plan.
    PlanResult add(std::uint64_t address, std::uint64_t size);
    const std::vector<GuestRegion>& regions() const { return regions_; }
    std::uint64_t page_size() const { return page_size_; }
    std::size_t region_count() const { return regions_.size(); }

private:
    std::uint64_t page_size_;
    std::vector<GuestRegion> regions_;
};

}  // namespace castlevania_ps4
