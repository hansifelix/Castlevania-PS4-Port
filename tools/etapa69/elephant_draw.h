/* Kazuma 69 — Vulkan procedural 2D mini-game. Original homebrew graphics, no game assets.
   Called from triangle68 derived from the PS4-tested Etapa 68.1 path. */
#ifndef KAZUMA69_DRAW_H
#define KAZUMA69_DRAW_H
#include <math.h>
#include <stdint.h>
#include <string.h>
#include <orbis/Pad.h>
#include <orbis/UserService.h>
#include "gameplay.h"

#define ELEPHANT69_CROSS 0x4000u

typedef struct {
    float rect[4];  /* x,y,width radius,height radius: NDC */
    float rgba[4];
    float extra[4]; /* shape: 0=rect, 1=oval */
} ElephantSprite;

static ElephantGame elephant_game;
static int elephant_pad = -1;
static uint32_t elephant_button_last = 0;

static void elephant_pad_start(void) {
    int user = -1;
    int init_user = sceUserServiceInitialize(NULL);
    int uid_status = sceUserServiceGetInitialUser(&user);
    int init_pad = scePadInit();
    if (uid_status == 0 && user >= 0) elephant_pad = scePadOpen(user, 0, 0, NULL);
    say("KAZUMA69: PAD_INIT=%d USER_INIT=%d USER_RESULT=%d PAD_HANDLE=%d",
        init_pad, init_user, uid_status, elephant_pad);
    if (elephant_pad < 0)
        say("KAZUMA69: PAD_FALHOU; cena vai continuar, X nao funcionara ate corrigir o pad");
}

static int elephant_pressed_x(void) {
    if (elephant_pad < 0) return 0;
    OrbisPadData data;
    memset(&data, 0, sizeof(data));
    int status = scePadReadState(elephant_pad, &data);
    if (status < 0) return 0;
    uint32_t b = data.buttons;
    int pressed = (b & ELEPHANT69_CROSS) != 0;
    if (pressed && !(elephant_button_last & ELEPHANT69_CROSS))
        say("KAZUMA69: CONTROLE_X_DETECTADO buttons=0x%08x", b);
    elephant_button_last = b;
    return pressed;
}

static void sprite(VkCommandBuffer c, VkPipelineLayout layout,
                   float x, float y, float rx, float ry,
                   float r, float g, float b, int shape) {
    ElephantSprite s = {
      .rect = {x,y,rx,ry}, .rgba = {r,g,b,1.f}, .extra={ (float)shape,0,0,0}
    };
    vkCmdPushConstants(c, layout,
       VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
       0, (uint32_t)sizeof(s), &s);
    vkCmdDraw(c, 6, 1, 0, 0);
}
#define RECT(C,L,X,Y,WX,WY,R,G,B) sprite(C,L,X,Y,WX,WY,R,G,B,0)
#define OVAL(C,L,X,Y,WX,WY,R,G,B) sprite(C,L,X,Y,WX,WY,R,G,B,1)

static void elephant_scene(VkCommandBuffer c, VkPipelineLayout layout,
                           const ElephantGame* st) {
    const float scroll = st->scroll;
    /* Sol, morros e gramado. Fundo e gerado sem imagens externas. */
    OVAL(c,layout, .76f,.69f,.12f,.12f, 1.0f,.87f,.41f);
    OVAL(c,layout, .76f,.69f,.085f,.085f, 1.0f,.94f,.63f);
    OVAL(c,layout,-.79f,-.60f,.76f,.54f, .23f,.57f,.44f);
    OVAL(c,layout, .32f,-.61f,.85f,.54f, .20f,.54f,.42f);
    OVAL(c,layout, 1.02f,-.58f,.70f,.54f, .26f,.61f,.43f);
    /* Arvores em perspectiva: avancam mais devagar que as cercas. */
    for (int i=0;i<9;i++) {
       float x=-1.25f+i*.34f-(scroll*.23f);
       while (x < -1.25f) x+=3.06f;
       RECT(c,layout,x,-.33f,.035f,.36f,.29f,.37f,.23f);
       RECT(c,layout,x-.065f,-.22f,.020f,.17f,.29f,.37f,.23f);
       OVAL(c,layout,x,.12f,.16f,.26f,.07f,.35f,.24f);
       OVAL(c,layout,x-.12f,.10f,.13f,.20f,.08f,.40f,.27f);
       OVAL(c,layout,x+.12f,.11f,.13f,.19f,.11f,.46f,.30f);
       OVAL(c,layout,x,.25f,.12f,.18f,.10f,.43f,.28f);
    }
    RECT(c,layout,0,-.82f,1.0f,.22f,.21f,.52f,.18f);
    RECT(c,layout,0,-.624f,1.0f,.031f,.42f,.73f,.24f);
    for (int i=0;i<21;i++) {
       float x = -1.2f+i*.115f-scroll*.62f;
       while(x < -1.1f) x +=2.415f;
       OVAL(c,layout,x,-.63f,.012f,.045f,.12f,.48f,.14f);
       OVAL(c,layout,x+.04f,-.65f,.012f,.03f,.13f,.52f,.15f);
    }
    /* Cercas moveis: travessas de madeira e postes. */
    for(int i=0;i<3;i++) {
       float x=st->fence[i];
       if(x < -1.12f || x>1.14f) continue;
       RECT(c,layout,x,-.49f,.12f,.024f,.38f,.20f,.09f);
       RECT(c,layout,x,-.57f,.12f,.023f,.48f,.28f,.13f);
       RECT(c,layout,x-.087f,-.51f,.019f,.155f,.65f,.41f,.19f);
       RECT(c,layout,x+.087f,-.51f,.019f,.155f,.65f,.41f,.19f);
       RECT(c,layout,x-.087f,-.36f,.030f,.025f,.74f,.48f,.20f);
       RECT(c,layout,x+.087f,-.36f,.030f,.025f,.74f,.48f,.20f);
    }
    /* Elefante correndo: corpo, patas animadas, tromba, orelha e presas. */
    float j=st->y;
    float run=st->y>.01f ? 0.f : sinf(st->time*24.f)*.023f;
    float bounce=st->y>.01f ? 0.f : .009f*sinf(st->time*24.f);
    const float x=-.52f;
    const float y=-.40f+j+bounce;
    /* Sombra permanece no chao durante o salto */
    OVAL(c,layout,x,-.66f,.23f,.025f,.13f,.34f,.18f);
    /* Rabinho */
    RECT(c,layout,x-.225f,y-.055f,.055f,.015f,.55f,.57f,.63f);
    OVAL(c,layout,x-.28f,y-.080f,.021f,.026f,.39f,.41f,.49f);
    /* Pernas atras */
    RECT(c,layout,x-.115f,y-.157f+run,.053f,.104f,.40f,.43f,.50f);
    RECT(c,layout,x+.085f,y-.156f-run,.051f,.109f,.44f,.46f,.52f);
    OVAL(c,layout,x-.115f,y-.247f+run,.067f,.029f,.37f,.40f,.47f);
    OVAL(c,layout,x+.085f,y-.252f-run,.068f,.031f,.40f,.42f,.49f);
    /* Barriga */
    OVAL(c,layout,x-.035f,y+.030f,.245f,.167f,.62f,.66f,.73f);
    OVAL(c,layout,x+.018f,y-.010f,.187f,.111f,.65f,.69f,.76f);
    /* Pernas da frente */
    RECT(c,layout,x-.070f,y-.175f-run,.053f,.088f,.57f,.60f,.68f);
    RECT(c,layout,x+.126f,y-.173f+run,.055f,.089f,.58f,.61f,.69f);
    OVAL(c,layout,x-.070f,y-.251f-run,.070f,.027f,.53f,.56f,.65f);
    OVAL(c,layout,x+.126f,y-.251f+run,.067f,.026f,.55f,.58f,.65f);
    /* Cabeca e focinho */
    OVAL(c,layout,x+.17f,y+.128f,.135f,.147f,.63f,.67f,.74f);
    /* Orelha grande rosada */
    OVAL(c,layout,x+.100f,y+.130f,.098f,.116f,.49f,.54f,.63f);
    OVAL(c,layout,x+.109f,y+.132f,.069f,.083f,.85f,.60f,.66f);
    /* Tromba em curva */
    OVAL(c,layout,x+.277f,y+.046f,.058f,.081f,.63f,.67f,.74f);
    RECT(c,layout,x+.288f,y-.034f,.044f,.100f,.62f,.66f,.74f);
    OVAL(c,layout,x+.322f,y-.130f,.055f,.043f,.59f,.63f,.72f);
    OVAL(c,layout,x+.354f,y-.113f,.020f,.029f,.69f,.72f,.78f);
    /* Presa e olho */
    OVAL(c,layout,x+.241f,y-.004f,.040f,.019f,1.0f,.96f,.79f);
    OVAL(c,layout,x+.219f,y+.173f,.018f,.021f,.99f,.98f,.92f);
    OVAL(c,layout,x+.224f,y+.175f,.009f,.012f,.07f,.09f,.14f);
    /* Indicador X no canto direito (dois tracos em pixel art). */
    OVAL(c,layout,.86f,.72f,.075f,.079f,.97f,.95f,.88f);
    RECT(c,layout,.84f,.74f,.012f,.018f,.27f,.36f,.54f);
    RECT(c,layout,.88f,.74f,.012f,.018f,.27f,.36f,.54f);
    RECT(c,layout,.86f,.72f,.012f,.018f,.27f,.36f,.54f);
    RECT(c,layout,.84f,.70f,.012f,.018f,.27f,.36f,.54f);
    RECT(c,layout,.88f,.70f,.012f,.018f,.27f,.36f,.54f);
    /* Barra de progresso: avancar por cercas, sem tipografia externa. */
    RECT(c,layout,-.72f,.83f,.245f,.020f,.18f,.33f,.28f);
    for(int i=0;i<7;i++) {
       float xbar=-.93f+.063f*i;
       if ((unsigned)i < (st->cleared%8)) RECT(c,layout,xbar,.83f,.025f,.013f,.97f,.84f,.33f);
    }
    if (st->damage_flash > 0.f) {
       OVAL(c,layout,-.82f,.70f,.09f,.035f,.98f,.24f,.16f);
    }
}
#endif
