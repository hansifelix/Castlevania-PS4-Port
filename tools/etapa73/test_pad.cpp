#include "pad_mapping.h"
#include <cassert>
#include <cstdio>
int main() {
    using namespace nx::plat;
    using namespace kazuma73;
    auto idle=translate({0,128,128,128,128,0,0});
    assert(!idle.buttons && idle.lx==0 && idle.ly==0);
    auto btn=translate({CROSS|CIRCLE|TRIANGLE|SQUARE|UP|L1|OPTIONS,128,128,128,128,0,0});
    assert(btn.buttons & kA); assert(btn.buttons & kB);
    assert(btn.buttons & kX);assert(btn.buttons & kY);
    assert(btn.buttons & kUp);assert(btn.buttons & kL);assert(btn.buttons & kPlus);
    auto axis=translate({0,255,0,0,255,250,250});
    assert(axis.lx>20000 && axis.ly>20000);
    assert(axis.rx< -20000 && axis.ry< -20000);
    assert(axis.buttons & kStickLRight);assert(axis.buttons & kStickLUp);
    assert(axis.buttons & kZL);assert(axis.buttons & kZR);
    puts("KAZUMA73: mapeamento DS4 -> Npad testado no Linux (SEM HARDWARE)");
}
