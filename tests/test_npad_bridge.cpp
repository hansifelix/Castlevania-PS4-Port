#include "runtime_bridge/npad_bridge.hpp"
#include "input_adapter.hpp"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <cstdint>
using namespace castlevania_ps4;

constexpr std::uint32_t bit(DS4 key) { return static_cast<std::uint32_t>(key); }

int main() {
    // Neutral pad and analogue dead-zone.
    const auto neutral = to_npad({});
    assert(neutral.buttons == 0 && neutral.lx == 0 && neutral.ly == 0);
    const auto small = to_npad({0, 10, -7848, 7848, 0});
    assert(small.lx == 0 && small.ly == 0 && small.rx == 0);

    // Match documented public nx::plat Npad masks, NOT the old 32-bit mask.
    assert(to_npad({bit(DS4::Cross)}).buttons == npad::A);
    assert(to_npad({bit(DS4::Circle)}).buttons == npad::B);
    assert(to_npad({bit(DS4::Cross)}, true).buttons == npad::B);
    assert(to_npad({bit(DS4::Circle)}, true).buttons == npad::A);
    assert(to_npad({bit(DS4::Triangle)}).buttons == npad::X);
    assert(to_npad({bit(DS4::Square)}).buttons == npad::Y);
    assert(to_npad({bit(DS4::L1)}).buttons == npad::L);
    assert(to_npad({bit(DS4::R1)}).buttons == npad::R);
    assert(to_npad({bit(DS4::L2)}).buttons == npad::ZL);
    assert(to_npad({bit(DS4::R2)}).buttons == npad::ZR);
    assert(to_npad({bit(DS4::L3)}).buttons == npad::StickL);
    assert(to_npad({bit(DS4::R3)}).buttons == npad::StickR);
    assert(to_npad({bit(DS4::Options)}).buttons == npad::Plus);
    assert(to_npad({bit(DS4::Touchpad)}).buttons == npad::Minus);
    assert(to_npad({bit(DS4::Left)}).buttons == npad::Left);
    assert(to_npad({bit(DS4::Right)}).buttons == npad::Right);
    assert(to_npad({bit(DS4::Up)}).buttons == npad::Up);
    assert(to_npad({bit(DS4::Down)}).buttons == npad::Down);

    const auto combo = to_npad({bit(DS4::Cross) | bit(DS4::Up) | bit(DS4::R2),
                                20000, -20000, 40000, -40000});
    assert(combo.buttons == (npad::A | npad::Up | npad::ZR));
    assert(combo.lx == 20000 && combo.ly == -20000);
    assert(combo.rx == 32767 && combo.ry == -32767);

    // All 16 mapped digital buttons are independent and give exactly 16 bits.
    const auto all = to_npad({0xFFFFu});
    assert(all.buttons == 0xFFFFu);
    // Unknown bits have no effect.
    assert(to_npad({0xFFFF0000u}).buttons == 0);
}
