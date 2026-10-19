#include "pad_translate.h"

namespace cvps4 {
namespace {
// OrbisPadButton values: OpenOrbis include/orbis/_types/pad.h.
constexpr uint32_t L3=0x0002, R3=0x0004, OPTIONS=0x0008;
constexpr uint32_t UP=0x0010, RIGHT=0x0020, DOWN=0x0040, LEFT=0x0080;
constexpr uint32_t L2=0x0100, R2=0x0200, L1=0x0400, R1=0x0800;
constexpr uint32_t TRIANGLE=0x1000, CIRCLE=0x2000, CROSS=0x4000, SQUARE=0x8000;
constexpr uint32_t TOUCH=0x100000;
int32_t axis(uint8_t raw, bool invert=false) {
    const int centered = int(raw) - 128;
    if (centered >= -12 && centered <= 12) return 0;
    int x = centered * 32767 / 127;
    if (x < -32767) x = -32767;
    if (x > 32767) x = 32767;
    return invert ? -x : x;
}
}  // namespace
nx::plat::PadState convert_pad(const RawPad& in) {
    using namespace nx::plat;
    PadState p{};
    if (!in.connected) return p;
    const auto b = in.buttons;
    // Switch A = east (Circle), B = south (Cross), X = north, Y = west.
    if (b & CIRCLE) p.buttons |= kA;
    if (b & CROSS) p.buttons |= kB;
    if (b & TRIANGLE) p.buttons |= kX;
    if (b & SQUARE) p.buttons |= kY;
    if (b & L1) p.buttons |= kL;
    if (b & R1) p.buttons |= kR;
    if (b & L2) p.buttons |= kZL;
    if (b & R2) p.buttons |= kZR;
    if (b & OPTIONS) p.buttons |= kPlus;
    if (b & TOUCH) p.buttons |= kMinus;
    if (b & L3) p.buttons |= kStickL;
    if (b & R3) p.buttons |= kStickR;
    if (b & UP) p.buttons |= kUp;
    if (b & DOWN) p.buttons |= kDown;
    if (b & LEFT) p.buttons |= kLeft;
    if (b & RIGHT) p.buttons |= kRight;
    p.lx = axis(in.lx); p.ly = axis(in.ly, true);
    p.rx = axis(in.rx); p.ry = axis(in.ry, true);
    return p;
}
}  // namespace cvps4
