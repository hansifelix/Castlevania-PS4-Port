#pragma once
#include <cstdint>

// Portability component 0.1 — NOT a game runtime.
// PS4 pad bit names are local to this adapter, so no Orbis SDK is needed for tests.
namespace castlevania_ps4 {

enum class DS4 : uint32_t {
    Cross = 1u << 0, Circle = 1u << 1, Square = 1u << 2, Triangle = 1u << 3,
    L1 = 1u << 4, R1 = 1u << 5, L2 = 1u << 6, R2 = 1u << 7,
    Options = 1u << 8, Touchpad = 1u << 9,
    Up = 1u << 10, Down = 1u << 11, Left = 1u << 12, Right = 1u << 13,
    L3 = 1u << 14, R3 = 1u << 15
};

enum class Switch : uint32_t {
    A = 1u << 0, B = 1u << 1, X = 1u << 2, Y = 1u << 3,
    L = 1u << 4, R = 1u << 5, ZL = 1u << 6, ZR = 1u << 7,
    Plus = 1u << 8, Minus = 1u << 9,
    Up = 1u << 10, Down = 1u << 11, Left = 1u << 12, Right = 1u << 13,
    LS = 1u << 14, RS = 1u << 15
};

// Default PS4-style face buttons: Cross=A (confirm), Circle=B (back),
// Square=Y, Triangle=X. Actual in-game actions still require verification.
// Optional Nintendo-physical layout: Cross=B, Circle=A.
// This is a pure mapping prototype, not connected to PS4 pad services.
uint32_t map_buttons(uint32_t ds4_buttons, bool nintendo_physical_layout = false);
}
