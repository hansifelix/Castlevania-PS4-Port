// Kazuma Port Games BR — Homebrew Test 02: DualShock 4 + memoria.
// Codigo proprio. Sem rotinas nem arquivos do Castlevania.
// Usa a mesma interface grafica livre que ja funcionou no Test 01.
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <sstream>
#include <orbis/libkernel.h>
#include <orbis/Pad.h>
#include <orbis/UserService.h>
#include <orbis/SystemService.h>
#include <orbis/Sysmodule.h>
#include "graphics.h"
#include "log.h"
#include "platform.h"  // contrato nx::plat original do upstream
extern "C" void kazuma_plat_attach_pad(int handle);
extern "C" int kazuma_probe_upstream();

std::stringstream debugLogStream;
struct Glyph { char ch; uint8_t rows[7]; };
static const Glyph GLYPHS[] = {
    {'A',{14,17,17,31,17,17,17}}, {'B',{30,17,17,30,17,17,30}},
    {'C',{14,17,16,16,16,17,14}}, {'D',{30,17,17,17,17,17,30}},
    {'E',{31,16,16,30,16,16,31}}, {'F',{31,16,16,30,16,16,16}},
    {'G',{14,17,16,23,17,17,14}}, {'H',{17,17,17,31,17,17,17}},
    {'I',{31,4,4,4,4,4,31}}, {'J',{7,2,2,2,18,18,12}},
    {'K',{17,18,20,24,20,18,17}}, {'L',{16,16,16,16,16,16,31}},
    {'M',{17,27,21,21,17,17,17}}, {'N',{17,25,21,19,17,17,17}},
    {'O',{14,17,17,17,17,17,14}}, {'P',{30,17,17,30,16,16,16}},
    {'Q',{14,17,17,17,21,18,13}}, {'R',{30,17,17,30,20,18,17}},
    {'S',{15,16,16,14,1,1,30}}, {'T',{31,4,4,4,4,4,4}},
    {'U',{17,17,17,17,17,17,14}}, {'V',{17,17,17,17,17,10,4}},
    {'W',{17,17,17,21,21,21,10}}, {'X',{17,17,10,4,10,17,17}},
    {'Y',{17,17,10,4,4,4,4}}, {'Z',{31,1,2,4,8,16,31}},
    {'0',{14,17,19,21,25,17,14}}, {'1',{4,12,4,4,4,4,14}},
    {'2',{14,17,1,2,4,8,31}}, {'3',{30,1,1,14,1,1,30}},
    {'4',{2,6,10,18,31,2,2}}, {'5',{31,16,30,1,1,17,14}},
    {'6',{6,8,16,30,17,17,14}}, {'7',{31,1,2,4,8,8,8}},
    {'8',{14,17,17,14,17,17,14}}, {'9',{14,17,17,15,1,2,12}},
    {':',{0,4,4,0,4,4,0}}, {'-',{0,0,0,31,0,0,0}},
    {'.',{0,0,0,0,0,12,12}}, {'/',{1,1,2,4,8,16,16}}
};
static const uint8_t* glyph(char c) {
    for (const auto &g : GLYPHS) if (g.ch == c) return g.rows;
    return nullptr;
}
static void text(Scene2D &s, const char *msg, int x, int y, int scale, Color color) {
    for (const char *p = msg; *p; ++p, x += 6 * scale) {
        const uint8_t *rows = glyph(*p);
        if (!rows) continue;
        for (int r = 0; r < 7; ++r)
            for (int col = 0; col < 5; ++col)
                if (rows[r] & (1u << (4-col)))
                    s.DrawRectangle(x + col*scale, y+r*scale, scale, scale, color);
    }
}
static void center(Scene2D &s, const char *str, int y, int scale, Color color) {
    int n=0; while(str[n]) ++n;
    text(s, str, (1920-n*6*scale)/2, y, scale, color);
}
static bool memory_test() {
    constexpr unsigned int size=64u*1024u;
    uint8_t *buf=(uint8_t*)std::malloc(size);
    if (!buf) return false;
    for (unsigned int i=0; i<size; ++i) buf[i]=(uint8_t)((i*17u+31u)&255u);
    bool ok=true;
    for (unsigned int i=0; i<size; ++i)
        if (buf[i]!=(uint8_t)((i*17u+31u)&255u)) {ok=false;break;}
    std::free(buf);
    return ok;
}
static const char* key_name(uint32_t b) {
    if (b & ORBIS_PAD_BUTTON_CROSS) return "X";
    if (b & ORBIS_PAD_BUTTON_SQUARE) return "QUADRADO";
    if (b & ORBIS_PAD_BUTTON_CIRCLE) return "O";
    if (b & ORBIS_PAD_BUTTON_TRIANGLE) return "TRIANGULO";
    if (b & ORBIS_PAD_BUTTON_UP) return "CIMA";
    if (b & ORBIS_PAD_BUTTON_DOWN) return "BAIXO";
    if (b & ORBIS_PAD_BUTTON_LEFT) return "ESQUERDA";
    if (b & ORBIS_PAD_BUTTON_RIGHT) return "DIREITA";
    if (b & ORBIS_PAD_BUTTON_OPTIONS) return "OPTIONS";
    if (b & ORBIS_PAD_BUTTON_L1) return "L1";
    if (b & ORBIS_PAD_BUTTON_R1) return "R1";
    if (b & ORBIS_PAD_BUTTON_L2) return "L2";
    if (b & ORBIS_PAD_BUTTON_R2) return "R2";
    return "OUTRO";
}
// Fixture sintetica empacotada em /app0 (somente leitura, sem dados de jogo).
static bool test_local_resource() {
    constexpr const char expected[] = "KAZUMA_STAGE16_RESOURCE_OK\n";
    FILE* f = nx::plat::fopen_utf8("/app0/kazuma_stage16.dat", "rb");
    if (!f) f = nx::plat::fopen_utf8("kazuma_stage16.dat", "rb");
    if (!f) return false;
    char content[sizeof(expected)+8]{};
    const size_t n = std::fread(content, 1, sizeof(content), f);
    std::fclose(f);
    return n == sizeof(expected)-1 &&
           std::memcmp(content,expected,sizeof(expected)-1)==0;
}
static void draw_static(Scene2D &s) {
    const Color bg={9,15,32}, cyan={52,195,235}, white={240,248,255}, blue={34,76,153};
    s.FrameBufferFill(bg);
    s.DrawRectangle(100,100,1720,10,cyan);
    s.DrawRectangle(100,965,1720,10,blue);
    s.DrawRectangle(210,200,1500,580,blue);
    s.DrawRectangle(222,212,1476,556,bg);
    center(s,"KAZUMA PORT GAMES BR",300,9,white);
    center(s,"HOMEBREW TEST 05",440,7,cyan);
}
static void draw_dynamic(Scene2D &s, bool controller, bool memory_ok,
                         const char *last, bool mode, bool nx_ok, bool plat_input_ok, bool plat_clock_ok, bool file_ok, unsigned frame) {
    const Color bg={9,15,32}, white={240,248,255}, cyan={52,195,235};
    const Color green={80,230,158}, red={235,100,100}, gold={252,208,92};
    const Color highlight=mode ? gold : cyan;
    s.DrawRectangle(245,490,1430,310,bg);
    s.DrawRectangle(130,815,1660,130,bg);
    center(s,controller ? "CONTROLE: CONECTADO" : "CONTROLE: INDISPONIVEL",
           495,4,controller ? green:red);
    char line[96];
    std::snprintf(line,sizeof(line),"ULTIMO BOTAO: %s",last);
    center(s,line,548,4,white);
    center(s,memory_ok ? "MEMORIA 64KB: OK" : "MEMORIA 64KB: FALHA",606,4,
           memory_ok ? green : red);
    center(s, nx_ok ? "NX RUNTIME CPU: OK" : "NX RUNTIME CPU: FALHA",665,3,nx_ok ? green:red);
    center(s, plat_clock_ok ? "NX PLAT TEMPO: OK" : "NX PLAT TEMPO: VERIFICANDO",705,3,plat_clock_ok ? green:gold);
    center(s, plat_input_ok ? "NX PLAT INPUT: OK" : "NX PLAT INPUT: APERTE X",745,3,plat_input_ok ? green:gold);
    center(s,file_ok ? "NX PLAT ARQUIVO: OK" : "NX PLAT ARQUIVO: FALHA",780,3,file_ok ? green:red);
    center(s,"X TROCA COR / QUADRADO TESTA MEMORIA",825,3,highlight);
    center(s,"O TENTA SAIR / PS FECHA PELO MENU",882,3,white);
    const Color pulse=(frame/35u)%2 ? green:highlight;
    s.DrawRectangle(850,805,220,14,pulse);
}
int main(void) {
    setvbuf(stdout,nullptr,_IONBF,0);
    std::puts("KAZUMA TEST 05: tela, pad e memoria.");
    auto *scene=new Scene2D(1920,1080,4);
    if (!scene->Init(0x4000000,2)) {
        std::puts("ERRO: inicializacao de video falhou.");
        return 2;
    }
    for (int i=0;i<2;++i) {scene->SetActiveFrameBuffer(i); draw_static(*scene);}
    bool memory_ok=memory_test();
    const bool file_ok=test_local_resource();
    bool nx_ok=(kazuma_probe_upstream()==1);
    bool pad_initialized=(scePadInit()==0);
    int pad=-1;
    if (pad_initialized) {
        OrbisUserServiceInitializeParams param{};
        param.priority=ORBIS_KERNEL_PRIO_FIFO_NORMAL;
        // Segue a ordem de inicializacao dos exemplos do OpenOrbis.
        int init_result=sceUserServiceInitialize(&param);
        int user_id=-1;
        if (init_result==0 && sceUserServiceGetInitialUser(&user_id)==0 && user_id>=0)
            pad=scePadOpen(user_id,ORBIS_PAD_PORT_TYPE_STANDARD,0,nullptr);
    }
    kazuma_plat_attach_pad(pad);
    bool input_seen=false;
    bool clock_ok=false;
    uint64_t prev_tick=nx::plat::monotonic_ns();
    bool theme=false;
    bool connected=false;
    uint32_t prev=0;
    const char* last="NENHUM";
    unsigned frame=0;
    for (;;) {
        if (pad>=0) {
            OrbisPadData data{};
            int read=scePadReadState(pad,&data);
            connected=(read>=0 && data.connected!=0);
            uint32_t curr=connected ? data.buttons:0;
            uint32_t pressed=curr & ~prev;
            prev=curr;
            if (pressed) last=key_name(pressed);
            if (pressed & ORBIS_PAD_BUTTON_CIRCLE) {
                // Evitar retornar de main(): no Test 02 antigo isso resultou
                // em CE-34878-0. Solicitar saida via servico do sistema.
                std::puts("KAZUMA TEST 05: solicitando retorno ao menu do PS4...");
                int module_rc = (int)sceSysmoduleLoadModuleInternal(
                    ORBIS_SYSMODULE_INTERNAL_SYSTEM_SERVICE);
                std::printf("SystemService load: %d\n", module_rc);
                if (module_rc == 0) {
                    int exit_rc = sceSystemServiceLoadExec("exit", nullptr);
                    std::printf("SystemServiceLoadExec retornou: %d\n", exit_rc);
                }
                // Se a requisicao retornar (falhar), NAO finalizar main.
                // Manter tela visivel para fechar manualmente com o botao PS.
                last = "USE BOTAO PS PARA FECHAR";
                connected = false;
                kazuma_plat_attach_pad(-1);
                scePadClose(pad);
                pad = -1;
            }
            if (pressed & ORBIS_PAD_BUTTON_CROSS) theme=!theme;
            if (pressed & ORBIS_PAD_BUTTON_SQUARE) memory_ok=memory_test();
        }
        // Contrato do runtime ORIGINAL, implementado via libScePad no PS4.
        // O botao X (DS4) corresponde a B (face inferior) no layout Switch.
        nx::plat::PadState nx_pad{};
        nx::plat::read_pad(nx_pad);
        if (nx_pad.buttons & nx::plat::kB) input_seen=true;
        const uint64_t now=nx::plat::monotonic_ns();
        if (now>prev_tick && prev_tick>0) clock_ok=true;
        prev_tick=now;
        scene->SetActiveFrameBuffer(int(frame%2u));
        draw_dynamic(*scene,connected,memory_ok,last,theme,nx_ok,input_seen,clock_ok,file_ok,frame);
        scene->SubmitFlip(int(frame));
        scene->FrameWait(int(frame));
        ++frame;
    }
    // A saida por Circulo e solicitada ao SystemService.
    return 0;
}
