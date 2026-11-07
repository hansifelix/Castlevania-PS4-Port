#include "port_core/guest_module_index.hpp"
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>

using namespace kazuma_port_core;

// Live assertions even in Release/with NDEBUG.
#define CHECK(condition) do { \
    if (!(condition)) { \
        std::fprintf(stderr, "FAILED %s:%d: %s\\n", __FILE__, __LINE__, #condition); \
        return EXIT_FAILURE; \
    } \
} while (false)

int main() {
    constexpr std::uint64_t page = 0x4000;
    GuestModuleIndex index(page);
    CHECK(index.page_size() == page);
    CHECK(index.add("sdk", 0x180000, 2 * page) == AddModuleResult::ok);
    CHECK(index.add("main", 0x100000, page) == AddModuleResult::ok);
    CHECK(index.add("subsdk0", 0x200000, page) == AddModuleResult::ok);
    CHECK(index.size() == 3);
    CHECK(index.modules()[0].name == "main");
    CHECK(index.modules()[1].name == "sdk");
    CHECK(index.modules()[2].name == "subsdk0");

    auto first = index.resolve(0x100000);
    CHECK(first.has_value());
    CHECK(first->module == "main" && first->offset == 0);
    auto last = index.resolve(0x103fff);
    CHECK(last.has_value());
    CHECK(last->module == "main" && last->offset == 0x3fff);
    CHECK(!index.resolve(0x104000).has_value());
    CHECK(!index.resolve(0x0fffff).has_value());
    auto sdk = index.resolve(0x187fff);
    CHECK(sdk.has_value());
    CHECK(sdk->module == "sdk" && sdk->offset == 0x7fff);
    CHECK(!index.resolve(0x188000).has_value());
    CHECK(!index.resolve(0xffffffffffffffffULL).has_value());
    CHECK(index.by_name("subsdk0")->base == 0x200000);
    CHECK(!index.by_name("absent").has_value());

    CHECK(index.add("", 0x300000, page) == AddModuleResult::empty_name);
    CHECK(index.add("main", 0x300000, page) == AddModuleResult::duplicate_name);
    CHECK(index.add("zero", 0x300000, 0) == AddModuleResult::zero_size);
    CHECK(index.add("unaligned", 0x300001, page) == AddModuleResult::misaligned);
    CHECK(index.add("size_misaligned", 0x300000, page - 1) == AddModuleResult::misaligned);
    CHECK(index.add("overlap", 0x180000, page) == AddModuleResult::overlaps);
    CHECK(index.size() == 3);  // rejects have no state change

    GuestModuleIndex invalid_pages(3);
    CHECK(invalid_pages.add("x", 0, 3) == AddModuleResult::invalid_page_size);
    GuestModuleIndex zero_pages(0);
    CHECK(zero_pages.add("x", 0, page) == AddModuleResult::invalid_page_size);
    GuestModuleIndex overflow(page);
    CHECK(overflow.add("high", std::numeric_limits<std::uint64_t>::max() - (page - 1), page)
          == AddModuleResult::address_overflow);
    CHECK(overflow.size() == 0);

    GuestModuleIndex adjacent(4096);
    CHECK(adjacent.add("a", 4096, 4096) == AddModuleResult::ok);
    CHECK(adjacent.add("b", 8192, 4096) == AddModuleResult::ok);
    CHECK(adjacent.resolve(8192)->module == "b");
    CHECK(adjacent.resolve(12287)->offset == 4095);
    CHECK(!adjacent.resolve(12288).has_value());

    std::puts("kazuma_port_core: guest module index OK (synthetic host test)");
    return EXIT_SUCCESS;
}
