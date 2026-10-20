#pragma once
#include <cstdint>

// Kazuma Port Games: host-only contract test for the Npad layout used by the
// public Belmont's Curse recompilation runtime. NO PS4 APIs / game code here.
namespace castlevania_ps4 {

// Buttons are bits from src/input_adapter.hpp (DS4), not scePad bit positions.
// Analog values are already signed, normalized to [-32767, 32767]; +Y is UP.
// A future PS4-specific adapter must convert scePad's raw axes and buttons.
struct Ds4Sample {
    std::uint32_t buttons = 0;
    std::int32_t lx = 0;
    std::int32_t ly = 0;
    std::int32_t rx = 0;
    std::int32_t ry = 0;
};

// Mirrors nx::plat::PadState's field types/order from the public runtime's
// runtime/src/platform.h. Do not claim binary compatibility without integration.
struct NpadSample {
    std::uint64_t buttons = 0;
    std::int32_t lx = 0;
    std::int32_t ly = 0;
    std::int32_t rx = 0;
    std::int32_t ry = 0;
};

namespace npad {
constexpr std::uint64_t A = 1ull << 0;
constexpr std::uint64_t B = 1ull << 1;
constexpr std::uint64_t X = 1ull << 2;
constexpr std::uint64_t Y = 1ull << 3;
constexpr std::uint64_t StickL = 1ull << 4;
constexpr std::uint64_t StickR = 1ull << 5;
constexpr std::uint64_t L = 1ull << 6;
constexpr std::uint64_t R = 1ull << 7;
constexpr std::uint64_t ZL = 1ull << 8;
constexpr std::uint64_t ZR = 1ull << 9;
constexpr std::uint64_t Plus = 1ull << 10;
constexpr std::uint64_t Minus = 1ull << 11;
constexpr std::uint64_t Left = 1ull << 12;
constexpr std::uint64_t Up = 1ull << 13;
constexpr std::uint64_t Right = 1ull << 14;
constexpr std::uint64_t Down = 1ull << 15;
} // namespace npad

// Unlike the existing 32-bit Switch:: mask, these 64-bit bits match the
// public runtime's NpadButton values; no actual game/runtime is linked here.
// nintendo_physical_layout=false matches src/input_adapter.hpp's default:
// Cross -> A, Circle -> B. True swaps them to Cross -> B, Circle -> A.
NpadSample to_npad(const Ds4Sample& sample, bool nintendo_physical_layout = false);
} // namespace castlevania_ps4
