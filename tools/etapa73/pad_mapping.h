#pragma once
// Traducao pura de estado DualShock 4 para Npad Nintendo do runtime nx.
// Fonte de bitfields: OpenOrbis <orbis/_types/pad.h>; contrato: upstream runtime/src/platform.h.
// Nao acessa hardware, usada tambem pelos testes Linux.
#include <cstdint>
#include "platform.h"

namespace kazuma73 {
struct Sample {
    uint32_t buttons;
    uint8_t lx,ly,rx,ry;
    uint8_t l2,r2;
};
constexpr uint32_t UP=0x0010, RIGHT=0x0020, DOWN=0x0040, LEFT=0x0080,
    L3=0x0002,R3=0x0004, OPTIONS=0x0008,
    L2=0x0100,R2=0x0200,L1=0x0400,R1=0x0800,
    TRIANGLE=0x1000,CIRCLE=0x2000,CROSS=0x4000,SQUARE=0x8000,
    TOUCH=0x100000;
// -32767 .. 32767; stick Y 0 no DS4 significa cima.
inline int32_t axis(uint8_t v, bool invert_y=false) {
    // zero centralizado em 128; clamp no extremo inferior para intervalo simetrico.
    int32_t t=(int32_t(v)-128)*257;
    if(t < -32767) t=-32767;
    if(t > 32767) t=32767;
    return invert_y?-t:t;
}
inline nx::plat::PadState translate(Sample d) {
    using namespace nx::plat;
    PadState p{};
    const uint32_t b=d.buttons;
    // DS4 circulo fica na direita = A Switch; cruz embaixo = B Switch.
    if (b&CIRCLE) p.buttons|=kA;
    if (b&CROSS) p.buttons|=kB;
    if (b&TRIANGLE) p.buttons|=kX;
    if (b&SQUARE) p.buttons|=kY;
    if (b&L1) p.buttons|=kL;
    if (b&R1) p.buttons|=kR;
    if ((b&L2)||d.l2>120) p.buttons|=kZL;
    if ((b&R2)||d.r2>120) p.buttons|=kZR;
    if (b&OPTIONS) p.buttons|=kPlus;
    if (b&TOUCH) p.buttons|=kMinus; // aproximacao documentada: touchpad para Minus.
    if (b&L3) p.buttons|=kStickL;
    if (b&R3) p.buttons|=kStickR;
    if (b&LEFT) p.buttons|=kLeft;
    if (b&UP) p.buttons|=kUp;
    if (b&RIGHT) p.buttons|=kRight;
    if (b&DOWN) p.buttons|=kDown;
    p.lx=axis(d.lx);p.ly=axis(d.ly,true);
    p.rx=axis(d.rx);p.ry=axis(d.ry,true);
    // Botoes direcionais dos analogicos virtuais sao informados sem substituir os eixos.
    constexpr int DEAD=11000;
    if(p.lx<-DEAD)p.buttons|=kStickLLeft;
    if(p.lx>DEAD)p.buttons|=kStickLRight;
    if(p.ly>DEAD)p.buttons|=kStickLUp;
    if(p.ly<-DEAD)p.buttons|=kStickLDown;
    if(p.rx<-DEAD)p.buttons|=kStickRLeft;
    if(p.rx>DEAD)p.buttons|=kStickRRight;
    if(p.ry>DEAD)p.buttons|=kStickRUp;
    if(p.ry<-DEAD)p.buttons|=kStickRDown;
    return p;
}
}
