#include "clock_math.h"
#include <cassert>
#include <cstdint>
int main() {
    using namespace kazuma47;
    assert(ticks_to_ns(0, 1000000) == 0);
    assert(ticks_to_ns(12000000, 1000000) == 12000000000ull);
    assert(ticks_to_ns(3300000, 1000000) == 3300000000ull);
    assert(ticks_to_ns(800000, 1600000000ull) == 500000ull);
    assert(ticks_to_ns(1, 0) == 0);
    assert(round_ns_to_us(0)==0);
    assert(round_ns_to_us(1)==1);
    assert(round_ns_to_us(999)==1);
    assert(round_ns_to_us(1000)==1);
    assert(round_ns_to_us(2000000)==2000);
    return 0;
}
