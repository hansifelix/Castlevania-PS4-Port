// Generic arithmetic-only preflight: never allocates guest memory.
// Not evidence of PS4 VA availability or nx::boot compatibility.
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <cstddef>
constexpr std::uint64_t GiB=1024ull*1024*1024;
constexpr std::uint64_t page=16384;
constexpr bool valid(std::uint64_t addr,std::uint64_t size) {
  return size!=0 && (addr%page)==0 && (size%page)==0 &&
         addr<=std::numeric_limits<std::uint64_t>::max()-size &&
         size<=static_cast<std::uint64_t>(SIZE_MAX) &&
         addr<=static_cast<std::uint64_t>(UINTPTR_MAX);
}
int main() {
  static_assert(valid(0x100000000ull,4*GiB));
  static_assert(valid(0x200000000ull,6*GiB));
  static_assert(valid(0x400000000ull,64*GiB));
  static_assert(!valid(0x100000001ull,4*GiB));
  static_assert(!valid(0x100000000ull,0));
  static_assert(!valid(std::numeric_limits<std::uint64_t>::max()-page+1,4*GiB));
  std::puts("LINGSHU_LARGE_RANGE_ARITHMETIC=PASS_HOST_ONLY_NO_ALLOCATION");
}
