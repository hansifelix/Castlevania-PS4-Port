#include "pad_translate.h"
#include <cassert>
#include <cstdio>

int main() {
    using namespace nx::plat;
    cvps4::RawPad raw{};
    auto p = cvps4::convert_pad(raw);
    assert(p.buttons == 0 && p.lx == 0);
    raw.connected = true;
    raw.buttons = 0x2000 | 0x4000 | 0x0010 | 0x0400 | 0x0100 | 0x0008;
    p = cvps4::convert_pad(raw);
    assert((p.buttons & (kA | kB | kUp | kL | kZL | kPlus)) == (kA | kB | kUp | kL | kZL | kPlus));
    raw.buttons = 0;
    raw.lx = 255; raw.ly = 0; raw.rx = 128; raw.ry = 255;
    p = cvps4::convert_pad(raw);
    assert(p.lx > 30000 && p.ly > 30000 && p.rx == 0 && p.ry < -30000);
    raw.lx = 120; raw.ly = 136;
    p = cvps4::convert_pad(raw);
    assert(p.lx == 0 && p.ly == 0);
    puts("DS4 -> Npad: testes de traducao aprovados (dados sintéticos)");
}
