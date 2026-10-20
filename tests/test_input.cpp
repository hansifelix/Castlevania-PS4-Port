#include "input_adapter.hpp"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <iostream>
using namespace castlevania_ps4;
static uint32_t ds4(DS4 x) { return static_cast<uint32_t>(x); }
static uint32_t sw(Switch x) { return static_cast<uint32_t>(x); }
int main() {
    assert(map_buttons(0) == 0);
    assert(map_buttons(ds4(DS4::Cross)) == sw(Switch::A));
    assert(map_buttons(ds4(DS4::Cross), true) == sw(Switch::B));
    assert(map_buttons(ds4(DS4::Circle)) == sw(Switch::B));
    assert(map_buttons(ds4(DS4::Circle), true) == sw(Switch::A));
    assert(map_buttons(ds4(DS4::Square)) == sw(Switch::Y));
    assert(map_buttons(ds4(DS4::Triangle)) == sw(Switch::X));
    assert(map_buttons(ds4(DS4::R2) | ds4(DS4::L1)) == (sw(Switch::ZR) | sw(Switch::L)));
    assert(map_buttons(ds4(DS4::Options) | ds4(DS4::Touchpad)) == (sw(Switch::Plus) | sw(Switch::Minus)));
    assert(map_buttons(ds4(DS4::Up)) == sw(Switch::Up));
    assert(map_buttons(ds4(DS4::L3) | ds4(DS4::R3)) == (sw(Switch::LS) | sw(Switch::RS)));
    std::cout << "Input adapter OK (11 checks).\n";
}
