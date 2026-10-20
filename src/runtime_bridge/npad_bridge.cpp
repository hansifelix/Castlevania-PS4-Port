#include "runtime_bridge/npad_bridge.hpp"
#include "input_adapter.hpp"

namespace castlevania_ps4 {
namespace {
constexpr std::int32_t kStickMax = 32767;
// Based on the dead-zone currently used by the public Linux host reference.
constexpr std::int32_t kDeadZone = 7849;

std::int32_t normalize_axis(std::int32_t axis) {
    if (axis > kStickMax) axis = kStickMax;
    if (axis < -kStickMax) axis = -kStickMax;
    return (axis > -kDeadZone && axis < kDeadZone) ? 0 : axis;
}

struct BitPair { Switch source; std::uint64_t target; };
constexpr BitPair kButtonMap[] = {
    {Switch::A, npad::A}, {Switch::B, npad::B},
    {Switch::X, npad::X}, {Switch::Y, npad::Y},
    {Switch::LS, npad::StickL}, {Switch::RS, npad::StickR},
    {Switch::L, npad::L}, {Switch::R, npad::R},
    {Switch::ZL, npad::ZL}, {Switch::ZR, npad::ZR},
    {Switch::Plus, npad::Plus}, {Switch::Minus, npad::Minus},
    {Switch::Left, npad::Left}, {Switch::Up, npad::Up},
    {Switch::Right, npad::Right}, {Switch::Down, npad::Down},
};
} // namespace

NpadSample to_npad(const Ds4Sample& sample, bool nintendo_physical_layout) {
    const std::uint32_t button_mask = map_buttons(sample.buttons, nintendo_physical_layout);
    NpadSample result;
    for (const auto& entry : kButtonMap) {
        if ((button_mask & static_cast<std::uint32_t>(entry.source)) != 0)
            result.buttons |= entry.target;
    }
    result.lx = normalize_axis(sample.lx);
    result.ly = normalize_axis(sample.ly);
    result.rx = normalize_axis(sample.rx);
    result.ry = normalize_axis(sample.ry);
    return result;
}
} // namespace castlevania_ps4
