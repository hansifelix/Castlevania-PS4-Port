// Kazuma Port Games BR — Etapa 45, homebrew de diagnostico SEM JOGO.
// Carrega apenas fixture sintetica propria em /app0. Nenhum save e alterado.
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <sstream>
#include <string>
#include <orbis/libkernel.h>
#include <orbis/Pad.h>
#include <orbis/UserService.h>
#include "platform.h"
#include "graphics.h"
#include "log.h"

std::stringstream debugLogStream; // requisitado pelo helper graphics.cpp
struct Glyph { char c; unsigned char p[7]; };
static const Glyph font[] = {
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
 {'.',{0,0,0,0,0,12,12}}, {'/',{1,1,2,4,8,16,16}},
 {'=',{0,31,0,31,0,0,0}}, {'?',{14,17,1,2,4,0,4}}
};
static const unsigned char* glyph(char c) {
 for (const auto& g:font) if(g.c==c) return g.p;
 return nullptr;
}
static void print(Scene2D& scene, const char* s,int x,int y,int scale,Color color) {
 for(const char* a=s;*a;a++,x+=6*scale) {
  auto* g=glyph(*a); if(!g)continue;
  for(int i=0;i<7;i++) for(int j=0;j<5;j++)
   if(g[i]&(1u<<(4-j))) scene.DrawRectangle(x+j*scale,y+i*scale,scale,scale,color);
 }
}
static void center(Scene2D& scene,const char* s,int y,int scale,Color color) {
 int n=0; while(s[n]) ++n;
 print(scene,s,(1920-n*6*scale)/2,y,scale,color);
}
static void diagnostics(bool& clock_ok,bool& file_ok,bool& invalid_path_rejected) {
 nx::plat::log_line("KAZUMA45: DIAG_START - pacote homebrew independente");
 const uint64_t start=nx::plat::monotonic_ns();
 nx::plat::sleep_ns(1000000); // 1 ms, fora do loop grafico
 const uint64_t end=nx::plat::monotonic_ns();
 clock_ok = start>0 && end>start;
 const std::string path="/app0/kazuma45.dat";
 FILE* f=nx::plat::fopen_utf8(path,"rb");
 if(f) {
  const int64_t initial=nx::plat::ftell64(f);
  const int seek_ok=nx::plat::fseek64(f,7,SEEK_SET);
  const int64_t advanced=nx::plat::ftell64(f);
  char buf[32]{};
  const uint64_t read=nx::plat::read_at(f,0,buf,24);
  const int64_t after=nx::plat::ftell64(f);
  file_ok = initial==0 && seek_ok==0 && advanced==7 && after==7
            && read==24 && std::memcmp(buf,"KAZUMA_STAGE45_READAT_OK",24)==0;
  std::fclose(f);
 }
 // Exercita validacao de entrada da oitava funcao sem criar pastas/saves.
 invalid_path_rejected = !nx::plat::make_dirs("");
 std::printf("KAZUMA45: RELOGIO=%s ARQUIVO=%s PASTA_VAZIA_REJEITADA=%s\n",
             clock_ok?"OK":"FALHA",file_ok?"OK":"FALHA",invalid_path_rejected?"OK":"FALHA");
 nx::plat::log_line("KAZUMA45: DIAG_END");
}
static void paint(Scene2D& s, bool clock_ok,bool file_ok,bool dirs_ok,bool pad,bool cross,unsigned frame) {
 const Color bg={13,15,29}, panel={29,38,58},gold={218,173,94}, white={244,238,225};
 const Color green={80,220,155},red={230,94,105}, muted={138,154,174};
 s.FrameBufferFill(bg);
 s.DrawRectangle(84,90,1752,8,gold);
 s.DrawRectangle(86,980,1748,5,gold);
 s.DrawRectangle(245,245,1430,665,panel);
 s.DrawRectangle(255,255,1410,645,bg);
 // Logo menor e discreta: a arte do jogo sera usada so quando sua interface existir.
 center(s,"KAZUMA PORT GAMES BR",136,4,gold);
 center(s,"PS4 - DIAGNOSTICO 08 APIS",298,5,white);
 center(s,clock_ok?"RELOGIO: OK":"RELOGIO: FALHA",429,4,clock_ok?green:red);
 center(s,file_ok?"ARQUIVO: OK":"ARQUIVO: FALHA",499,4,file_ok?green:red);
 center(s,dirs_ok?"PASTA INVALIDA: REJEITADA":"PASTA INVALIDA: FALHA",569,3,dirs_ok?green:red);
 center(s,pad?"CONTROLE: CONECTADO":"CONTROLE: INDISPONIVEL",639,3,pad?green:red);
 center(s,cross?"X: RECEBIDO":"APERTE X PARA TESTAR",710,3,cross?green:muted);
 center(s,"SEM CASTLEVANIA - SEM DADOS COMERCIAIS",806,3,muted);
 center(s,"QUADRADO: REPETIR TESTES / PS: FECHAR",932,3,white);
 const Color pulse=(frame/40)%2?green:gold;
 s.DrawRectangle(860,858,200,9,pulse);
}
int main() {
 setvbuf(stdout,nullptr,_IONBF,0);
 std::puts("KAZUMA45: BOOT teste PS4 nativo 08 APIs, SEM JOGO");
 bool clock_ok=false, file_ok=false,dirs_ok=false;
 diagnostics(clock_ok,file_ok,dirs_ok);
 auto* scene=new Scene2D(1920,1080,4);
 if(!scene->Init(0x4000000,2)) {
   std::puts("KAZUMA45: VIDEO_INIT_FALHOU");return 2;
 }
 bool pad_ready = scePadInit()==0;
 int pad=-1;
 if(pad_ready) {
  OrbisUserServiceInitializeParams params{};
  params.priority=ORBIS_KERNEL_PRIO_FIFO_NORMAL;
  if(sceUserServiceInitialize(&params)==0) {
   int user=-1;
   if(sceUserServiceGetInitialUser(&user)==0 && user>=0)
     pad=scePadOpen(user,ORBIS_PAD_PORT_TYPE_STANDARD,0,nullptr);
  }
 }
 uint32_t previous=0; bool connected=false,seen_x=false;
 for(unsigned frame=0;;frame++) {
  if(pad>=0) {
   OrbisPadData d{};
   const int rc=scePadReadState(pad,&d);
   connected=rc>=0 && d.connected;
   const uint32_t curr=connected?d.buttons:0;
   const uint32_t newly=curr & ~previous;
   previous=curr;
   if(newly & ORBIS_PAD_BUTTON_CROSS) {
     seen_x=true;std::puts("KAZUMA45: BOTAO_X_RECEBIDO");
   }
   if(newly & ORBIS_PAD_BUTTON_SQUARE) diagnostics(clock_ok,file_ok,dirs_ok);
  }
  scene->SetActiveFrameBuffer(int(frame%2));
  paint(*scene,clock_ok,file_ok,dirs_ok,connected,seen_x,frame);
  scene->SubmitFlip(int(frame));
  scene->FrameWait(int(frame));
 }
}
