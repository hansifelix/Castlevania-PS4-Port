#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "runtime_bridge/guest_memory_plan.hpp"

// Game-neutral, host-testable part of Kazuma Port Core.
// Does not allocate memory, load proprietary modules or call PS4 APIs.
namespace kazuma_port_core {

struct GuestModule {
    std::string name;
    std::uint64_t base;
    std::uint64_t size;
};

struct ResolvedAddress {
    std::string module;
    std::uint64_t offset;
};

enum class AddModuleResult {
    ok,
    empty_name,
    duplicate_name,
    zero_size,
    invalid_page_size,
    misaligned,
    address_overflow,
    overlaps
};

const char* add_module_result_name(AddModuleResult result);

class GuestModuleIndex {
public:
    explicit GuestModuleIndex(std::uint64_t page_size);
    AddModuleResult add(const std::string& name, std::uint64_t base,
                        std::uint64_t size);
    std::optional<ResolvedAddress> resolve(std::uint64_t guest_address) const;
    std::optional<GuestModule> by_name(const std::string& name) const;
    const std::vector<GuestModule>& modules() const { return modules_; }
    std::size_t size() const { return modules_.size(); }
    std::uint64_t page_size() const { return plan_.page_size(); }

private:
    castlevania_ps4::GuestMemoryPlan plan_;
    std::vector<GuestModule> modules_; // sorted by base; entries are invalidated on add
};

}  // namespace kazuma_port_core
