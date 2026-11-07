#include "port_core/aot_text_bounds.hpp"
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <vector>
using namespace kazuma_port_core;

#define CHECK(cond) do { \
    if (!(cond)) { \
        std::fprintf(stderr, "FAILED %s:%d: %s\\n", __FILE__, __LINE__, #cond); \
        return EXIT_FAILURE; \
    } \
} while (false)

int main() {
    GuestModuleIndex idx(0x4000);
    CHECK(idx.add("main", 0x100000, 0x40000) == AddModuleResult::ok);
    CHECK(idx.add("subsdk0", 0x200000, 0x80000) == AddModuleResult::ok);
    auto check = [&](std::uint64_t start, std::uint64_t size,
                     const std::vector<std::uint64_t>& funcs) {
        return check_aot_text_bounds(idx, "subsdk0", start, size, funcs);
    };
    auto good = check(0x4000, 0x20000, {0x4000, 0x4004, 0x5000, 0x23ffc});
    CHECK(good.status == AotBoundsStatus::ok && good.checked == 4);
    CHECK(check(0x4000, 0x20000, {0x4000, 0x4000}).status ==
          AotBoundsStatus::duplicate_function);
    CHECK(check(0x4000, 0x20000, {0x5000, 0x4000}).status ==
          AotBoundsStatus::out_of_order_function);
    CHECK(check(0x4000, 0x20000, {0x4002}).status ==
          AotBoundsStatus::misaligned_function);
    CHECK(check(0x4000, 0x20000, {0x3ffc}).status ==
          AotBoundsStatus::outside_text_span);
    CHECK(check(0x4000, 0x20000, {0x24000}).status ==
          AotBoundsStatus::outside_text_span);
    CHECK(check(0x4000, 0x20000, {}).status ==
          AotBoundsStatus::empty_function_table);
    CHECK(check(0x4000, 0x0, {0x4000}).status ==
          AotBoundsStatus::invalid_text_span);
    CHECK(check(0x4002, 0x4000, {0x4004}).status ==
          AotBoundsStatus::invalid_text_span);
    CHECK(check(0x4000, 0x4001, {0x4000}).status ==
          AotBoundsStatus::invalid_text_span);
    CHECK(check(0x7c000, 0x8000, {0x7c000}).status ==
          AotBoundsStatus::invalid_text_span);
    CHECK(check(std::numeric_limits<std::uint64_t>::max(), 0x4000, {0x4000}).status ==
          AotBoundsStatus::invalid_text_span);
    CHECK(check_aot_text_bounds(idx, "sdk", 0, 0x4000, {0}).status ==
          AotBoundsStatus::unknown_module);
    CHECK(check_aot_text_bounds(idx, "main", 0x0, 0x4000, {0}).status ==
          AotBoundsStatus::ok);
    CHECK(idx.size() == 2); // Checker never changes module index.
    CHECK(aot_bounds_status_name(AotBoundsStatus::ok)[0] == 'o');

    std::puts("kazuma_port_core: AOT function text bounds OK (synthetic host test)");
    return EXIT_SUCCESS;
}
