#include "input_adapter.hpp"

namespace castlevania_ps4 {
uint32_t map_buttons(uint32_t p, bool nintendo_physical_layout) {
    struct Pair { DS4 from; Switch to; };
    const Pair mapping[] = {
        {DS4::Cross, nintendo_physical_layout ? Switch::B : Switch::A},
        {DS4::Circle, nintendo_physical_layout ? Switch::A : Switch::B},
        {DS4::Square, Switch::Y}, {DS4::Triangle, Switch::X},
        {DS4::L1, Switch::L}, {DS4::R1, Switch::R},
        {DS4::L2, Switch::ZL}, {DS4::R2, Switch::ZR},
        {DS4::Options, Switch::Plus}, {DS4::Touchpad, Switch::Minus},
        {DS4::Up, Switch::Up}, {DS4::Down, Switch::Down},
        {DS4::Left, Switch::Left}, {DS4::Right, Switch::Right},
        {DS4::L3, Switch::LS}, {DS4::R3, Switch::RS}
    };
    uint32_t result = 0;
    for (const auto &entry : mapping) {
        if (p & static_cast<uint32_t>(entry.from))
            result |= static_cast<uint32_t>(entry.to);
    }
    return result;
}
}
