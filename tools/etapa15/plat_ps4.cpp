// Kazuma Etapa 15: SUBCONJUNTO PS4 das interfaces originais nx::plat.
// Esta nao e uma implementacao completa da camada de plataforma do jogo.
// Le somente o DualShock 4 atribuido ao aplicativo e o relogio do processo.
#include "platform.h"   // extraido na CI de fonte PUBLICA, commit fixado
#include <orbis/Pad.h>
#include <orbis/libkernel.h>
#include <cstdint>

namespace {
int g_kazuma_pad_handle = -1;
static int32_t normalize_axis(uint8_t v, bool invert) {
    const int32_t raw = (int32_t(v) - 128) * 256;
    int32_t clipped = raw < -32767 ? -32767 : (raw > 32767 ? 32767 : raw);
    return invert ? -clipped : clipped;
}
}

// O fluxo de inicializacao de ScePad continua concentrado no Test 04.
extern "C" void kazuma_plat_attach_pad(int handle) {
    g_kazuma_pad_handle = handle;
}

namespace nx::plat {
uint64_t monotonic_ns() {
    // O OpenOrbis expõe esta funcao em microssegundos desde inicio do processo.
    return sceKernelGetProcessTime() * 1000ull;
}
void read_pad(PadState& out) {
    out = PadState{};
    if (g_kazuma_pad_handle < 0) return;
    OrbisPadData state{};
    const int rc = scePadReadState(g_kazuma_pad_handle, &state);
    if (rc < 0 || !state.connected) return;
    const uint32_t b=state.buttons;
    // Layout Nintendo: A direita, B embaixo, X em cima, Y a esquerda.
    if (b & ORBIS_PAD_BUTTON_CIRCLE) out.buttons |= kA;
    if (b & ORBIS_PAD_BUTTON_CROSS) out.buttons |= kB;
    if (b & ORBIS_PAD_BUTTON_TRIANGLE) out.buttons |= kX;
    if (b & ORBIS_PAD_BUTTON_SQUARE) out.buttons |= kY;
    if (b & ORBIS_PAD_BUTTON_OPTIONS) out.buttons |= kPlus;
    if (b & ORBIS_PAD_BUTTON_UP) out.buttons |= kUp;
    if (b & ORBIS_PAD_BUTTON_DOWN) out.buttons |= kDown;
    if (b & ORBIS_PAD_BUTTON_LEFT) out.buttons |= kLeft;
    if (b & ORBIS_PAD_BUTTON_RIGHT) out.buttons |= kRight;
    if (b & ORBIS_PAD_BUTTON_L1) out.buttons |= kL;
    if (b & ORBIS_PAD_BUTTON_R1) out.buttons |= kR;
    if (b & ORBIS_PAD_BUTTON_L2) out.buttons |= kZL;
    if (b & ORBIS_PAD_BUTTON_R2) out.buttons |= kZR;
    if (b & ORBIS_PAD_BUTTON_L3) out.buttons |= kStickL;
    if (b & ORBIS_PAD_BUTTON_R3) out.buttons |= kStickR;
    out.lx=normalize_axis(state.leftStick.x, false);
    out.ly=normalize_axis(state.leftStick.y, true);
    out.rx=normalize_axis(state.rightStick.x, false);
    out.ry=normalize_axis(state.rightStick.y, true);
}
} // namespace nx::plat
