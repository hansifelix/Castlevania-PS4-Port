// Actual PS4 implementation of the upstream nx::plat::read_pad interface.
// No SDL, Android touch overlay or game assets.
#include "pad_translate.h"
#include <orbis/Pad.h>
#include <orbis/UserService.h>

namespace {
int g_pad = -1;
bool init_pad() {
    if (g_pad >= 0) return true;
    if (scePadInit() < 0) return false;
    (void)sceUserServiceInitialize(nullptr);
    int32_t user_id = -1;
    if (sceUserServiceGetInitialUser(&user_id) < 0) return false;
    g_pad = scePadOpen(user_id, ORBIS_PAD_PORT_TYPE_STANDARD, 0, nullptr);
    return g_pad >= 0;
}
}  // namespace

namespace nx::plat {
void read_pad(PadState& p) {
    p = PadState{};
    if (!init_pad()) return;
    OrbisPadData data{};
    if (scePadReadState(g_pad, &data) < 0) return;
    cvps4::RawPad raw{};
    raw.buttons = data.buttons;
    raw.lx = data.leftStick.x;
    raw.ly = data.leftStick.y;
    raw.rx = data.rightStick.x;
    raw.ry = data.rightStick.y;
    raw.connected = data.connected != 0;
    p = cvps4::convert_pad(raw);
}
}
