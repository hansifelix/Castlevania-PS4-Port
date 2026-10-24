// Adapter nx::plat::read_pad para hardware real (scePad) usado no prototipo 69.
// O runtime nao recebe um controle 'falso': sem dispositivo, estado zerado.
// Revisao desta etapa: somente ligacao/compilacao no CI; hardware futuro.
#include <orbis/Pad.h>
#include <orbis/UserService.h>
#include <cstdint>
#include "platform.h"
#include "pad_mapping.h"

namespace nx::plat {
namespace {
int g_pad_handle=-1;
bool g_attempted=false;
int try_pad() {
    if(g_attempted) return g_pad_handle;
    g_attempted=true;
    (void)sceUserServiceInitialize(nullptr);
    int32_t user=-1;
    if(sceUserServiceGetInitialUser(&user)!=0 || user<0) return -1;
    if(scePadInit()<0) return -1;
    g_pad_handle=scePadOpen(user,0,0,nullptr);
    return g_pad_handle;
}
}
void read_pad(PadState& out) {
    out=PadState{};
    const int h=try_pad();
    if(h<0) return;
    OrbisPadData data{};
    const int status=scePadReadState(h,&data);
    if(status<0 || !data.connected) return;
    out=kazuma73::translate({data.buttons,
        data.leftStick.x,data.leftStick.y,data.rightStick.x,data.rightStick.y,
        data.analogButtons.l2,data.analogButtons.r2});
}
} // nx::plat
