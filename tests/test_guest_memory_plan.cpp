#include "runtime_bridge/guest_memory_plan.hpp"
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>

using namespace castlevania_ps4;

// Real assertions in both Debug and Release (no NDEBUG dependence).
#define CHECK(condition) do { \
    if (!(condition)) { \
        std::fprintf(stderr, "FAILED %s:%d: %s\n", __FILE__, __LINE__, #condition); \
        return EXIT_FAILURE; \
    } \
} while (false)

int main() {
    constexpr std::uint64_t p = 0x4000; // Test fixture only: not a claim about actual guest layout.
    GuestMemoryPlan plan(p);
    CHECK(plan.region_count() == 0);
    CHECK(plan.add(0x100000, 2*p) == PlanResult::ok);
    CHECK(plan.add(0x200000, p) == PlanResult::ok);
    CHECK(plan.add(0x0, p) == PlanResult::ok);
    CHECK(plan.add(0x100000 + p, p) == PlanResult::overlaps);
    CHECK(plan.add(0x100000, p) == PlanResult::overlaps);
    CHECK(plan.add(0x100000 - p, 2*p) == PlanResult::overlaps);
    CHECK(plan.add(0x100000 + 2*p, p) == PlanResult::ok); // adjacent is valid
    CHECK(plan.add(0x100001, p) == PlanResult::misaligned);
    CHECK(plan.add(0x300000, p-1) == PlanResult::misaligned);
    CHECK(plan.add(0x300000, 0) == PlanResult::zero_size);
    CHECK(plan.region_count() == 4); // rejected requests had no side effects
    CHECK(plan.regions()[0].begin == 0x0);
    CHECK(plan.regions()[1].begin == 0x100000);
    CHECK(plan.regions()[2].begin == 0x100000 + 2*p);
    CHECK(plan.regions()[3].begin == 0x200000);

    GuestMemoryPlan wrong(3);
    CHECK(wrong.add(0, 3) == PlanResult::invalid_page_size);
    GuestMemoryPlan zero(0);
    CHECK(zero.add(0, p) == PlanResult::invalid_page_size);
    GuestMemoryPlan high(p);
    CHECK(high.add(std::numeric_limits<std::uint64_t>::max() - (p-1), p)
          == PlanResult::address_overflow);
    CHECK(high.region_count() == 0);
    GuestMemoryPlan four_k(4096);
    CHECK(four_k.add(0, 4096) == PlanResult::ok);
    CHECK(four_k.add(4096, 4096) == PlanResult::ok);
    CHECK(four_k.add(8192, 4096) == PlanResult::ok);

    std::puts("guest_memory_plan: OK (host-only planner; no PS4 memory allocated)");
    return EXIT_SUCCESS;
}
