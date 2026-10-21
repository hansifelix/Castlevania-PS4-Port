// Kazuma Port Games BR - PS4 Homebrew Test 01.
// Codigo proprio, nao inclui recursos ou rotinas comerciais do Castlevania.
// Renderizacao de texto em matriz de pixels: nao necessita de fontes externas.
#include <cstdint>
#include <cstdio>
#include <sstream>
#include <orbis/libkernel.h>
#include "graphics.h"  // _common/graphics.h do OpenOrbis, rev. fixa
#include "log.h"

std::stringstream debugLogStream;  // Dependencia de _common/graphics.cpp

struct Glyph { char ch; uint8_t rows[7]; };
static const Glyph GLYPHS[] = {
    {'A',{14,17,17,31,17,17,17}}, {'B',{30,17,17,30,17,17,30}},
    {'C',{14,17,16,16,16,17,14}}, {'D',{30,17,17,17,17,17,30}},
    {'E',{31,16,16,30,16,16,31}}, {'F',{31,16,16,30,16,16,16}},
    {'G',{14,17,16,23,17,17,14}}, {'H',{17,17,17,31,17,17,17}},
    {'I',{31,4,4,4,4,4,31}},    {'J',{7,2,2,2,18,18,12}},
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
    {'.',{0,0,0,0,0,12,12}}, {'/',{1,1,2,4,8,16,16}},
};

static const uint8_t* glyph(char c) {
    for (const auto &g : GLYPHS) if (g.ch == c) return g.rows;
    return nullptr;  // espaco ou glifo indisponivel
}

static void text(Scene2D &s, const char *msg, int x, int y, int scale, Color color) {
    for (const char *p = msg; *p; ++p, x += 6 * scale) {
        const uint8_t *rows = glyph(*p);
        if (!rows) continue;
        for (int r = 0; r < 7; ++r)
            for (int col = 0; col < 5; ++col)
                if (rows[r] & (1u << (4 - col)))
                    s.DrawRectangle(x + col * scale, y + r * scale, scale, scale, color);
    }
}

static void centered(Scene2D &s, const char *msg, int y, int scale, Color color) {
    size_t n = 0; while (msg[n]) ++n;
    int x = (1920 - int(n * 6 * scale)) / 2;
    text(s, msg, x, y, scale, color);
}

static void paint(Scene2D &s) {
    const Color bg = { 9, 15, 32 };
    const Color cyan = { 52, 195, 235 };
    const Color white = { 240, 248, 255 };
    const Color blue = { 34, 76, 153 };
    const Color green = { 80, 230, 158 };
    s.FrameBufferFill(bg);
    s.DrawRectangle(100, 100, 1720, 10, cyan);
    s.DrawRectangle(100, 965, 1720, 10, blue);
    s.DrawRectangle(210, 200, 1500, 580, blue);
    s.DrawRectangle(222, 212, 1476, 556, bg);
    centered(s, "KAZUMA PORT GAMES BR", 300, 9, white);
    centered(s, "HOMEBREW TEST 01", 440, 7, cyan);
    centered(s, "VIDEO INICIALIZADO", 570, 6, green);
    centered(s, "SEM JOGO E SEM CASTLEVANIA", 690, 4, white);
    centered(s, "USE O BOTAO PS PARA FECHAR PELO MENU", 855, 3, white);
}

int main(void) {
    setvbuf(stdout, nullptr, _IONBF, 0);
    std::printf("KAZUMA ETAPA12: iniciando teste grafico independente.\n");
    auto *scene = new Scene2D(1920, 1080, 4);
    if (!scene->Init(0x4000000, 2)) {
        std::printf("KAZUMA ETAPA12: falha na inicializacao de video.\n");
        return 2;
    }
    for (int i = 0; i < 2; ++i) {
        scene->SetActiveFrameBuffer(i);
        paint(*scene);
    }
    unsigned frame = 0;
    for (;;) {
        scene->SetActiveFrameBuffer(int(frame % 2));
        const Color pulse = (frame / 45) % 2 ? Color{80,230,158} : Color{40,80,160};
        scene->DrawRectangle(850, 790, 220, 14, pulse);
        scene->SubmitFlip(int(frame));
        scene->FrameWait(int(frame));
        ++frame;
    }
}
