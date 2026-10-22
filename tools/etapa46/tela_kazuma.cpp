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
 nx::plat::log_line("KAZUMA46: DIAG_START - pacote homebrew independente");
 // O boot da Etapa 45 falhou uma vez e passou ao repetir: registrar tentativas.
 // O clock_monotonic e o nanosleep sao testados juntos, sem presumir a causa.
 clock_ok=false;
 for (int attempt=1; attempt<=4; ++attempt) {
  const uint64_t start=nx::plat::monotonic_ns();
  nx::plat::sleep_ns(2000000); // 2 ms
  const uint64_t end=nx::plat::monotonic_ns();
  std::printf("KAZUMA46: CLOCK_TENTATIVA=%d START_NS=%llu END_NS=%llu DELTA_NS=%llu\n",
    attempt,(unsigned long long)start,(unsigned long long)end,
    (unsigned long long)(end>start ? end-start : 0));
  if (start>0 && end>start) { clock_ok=true;break; }
 }
 file_ok=false;
 const std::string path="/app0/kazuma46.dat";
 FILE* f=nx::plat::fopen_utf8(path,"rb");
 if(f) {
  const int64_t initial=nx::plat::ftell64(f);
  const int seek_ok=nx::plat::fseek64(f,7,SEEK_SET);
  const int64_t advanced=nx::plat::ftell64(f);
  char buf[32]{};
  const uint64_t read=nx::plat::read_at(f,0,buf,24);
  const int64_t after=nx::plat::ftell64(f);
  file_ok = initial==0 && seek_ok==0 && advanced==7 && after==7
            && read==24 && std::memcmp(buf,"KAZUMA_STAGE46_READAT_OK",24)==0;
  std::fclose(f);
 }
 // Exercita validacao de entrada da oitava funcao sem criar pastas/saves.
 invalid_path_rejected = !nx::plat::make_dirs("");
 std::printf("KAZUMA46: RELOGIO=%s ARQUIVO=%s PASTA_VAZIA_REJEITADA=%s\n",
             clock_ok?"OK":"FALHA",file_ok?"OK":"FALHA",invalid_path_rejected?"OK":"FALHA");
 nx::plat::log_line("KAZUMA46: DIAG_END");
}
// Mede o tempo do frame COMPLETO deste homebrew (draw + flip + espera).
// Nao representa FPS do motor ou do jogo Castlevania.
struct PerfStats {
 uint64_t accumulated=0, worst=0;
 unsigned collected=0, spikes=0, fps10=0, avg_ms10=0, max_ms10=0, total_spikes=0;
 bool ready=false;
};
static void record_frame(PerfStats& p, uint64_t ns) {
 if(ns==0 || ns>5000000000ull) return;
 p.accumulated += ns;
 if(ns>p.worst)p.worst=ns;
 if(ns>40000000ull)++p.spikes;
 if(++p.collected==120) {
  p.fps10=(unsigned)((uint64_t)p.collected*10000000000ull/p.accumulated);
  p.avg_ms10=(unsigned)(p.accumulated/p.collected/100000ull);
  p.max_ms10=(unsigned)(p.worst/100000ull);
  p.total_spikes=p.spikes;
  p.ready=true;
  std::printf("KAZUMA46: PERF FPS_X10=%u AVG_MS_X10=%u MAX_MS_X10=%u FRAMES_GT40MS=%u\n",
    p.fps10,p.avg_ms10,p.max_ms10,p.total_spikes);
  p.accumulated=0;p.collected=0;p.worst=0;p.spikes=0;
 }
}
static void paint(Scene2D& s, bool clock_ok,bool file_ok,bool dirs_ok,bool pad,bool cross,
                  bool heavy,const PerfStats& perf,unsigned frame) {
 const Color bg={13,15,29}, panel={29,38,58},gold={218,173,94}, white={244,238,225};
 const Color green={80,220,155},red={230,94,105}, muted={138,154,174};
 s.FrameBufferFill(bg);
 s.DrawRectangle(84,90,1752,8,gold);
 s.DrawRectangle(86,980,1748,5,gold);
 s.DrawRectangle(245,245,1430,665,panel);
 s.DrawRectangle(255,255,1410,645,bg);
 if(heavy) {
  // Desenho sintetico: stress CPU/2D, sem geometria, assets ou motor do jogo.
  for(unsigned i=0;i<1600u;++i) {
   const int x=300+int((i*97u)%1250u);
   const int y=320+int((i*43u)%520u);
   s.DrawRectangle(x,y,16,8,(i&1u)?gold:muted);
  }
 }
 // Logo menor e discreta: a arte do jogo sera usada so quando sua interface existir.
 center(s,"KAZUMA PORT GAMES BR",136,4,gold);
 center(s,"PS4 - BENCHMARK DE INFRAESTRUTURA",290,4,white);
 center(s,clock_ok?"RELOGIO: OK":"RELOGIO: FALHA",408,4,clock_ok?green:red);
 center(s,file_ok?"ARQUIVO: OK":"ARQUIVO: FALHA",468,4,file_ok?green:red);
 center(s,dirs_ok?"PASTA INVALIDA: REJEITADA":"PASTA INVALIDA: FALHA",528,3,dirs_ok?green:red);
 center(s,pad?"CONTROLE: CONECTADO":"CONTROLE: INDISPONIVEL",588,3,pad?green:red);
 center(s,cross?"X: RECEBIDO":"APERTE X PARA TESTAR",647,3,cross?green:muted);
 char perfline[110];
 if(perf.ready) {
  std::snprintf(perfline,sizeof(perfline),"FPS: %u.%u  MED: %u.%u MS  MAX: %u.%u MS",
    perf.fps10/10,perf.fps10%10,perf.avg_ms10/10,perf.avg_ms10%10,
    perf.max_ms10/10,perf.max_ms10%10);
  center(s,perfline,723,3,green);
  std::snprintf(perfline,sizeof(perfline),"ATRASOS 40MS: %u  MODO: %s",perf.total_spikes,heavy?"CARGA":"NORMAL");
  center(s,perfline,770,3,white);
 } else center(s,"MEDINDO 120 QUADROS...",723,3,muted);
 center(s,"FPS DO HOMEBREW - NAO DO CASTLEVANIA",834,3,muted);
 center(s,"TRIANGULO: CARGA / QUADRADO: TESTES / PS: SAIR",932,3,white);
 const Color pulse=(frame/40)%2?green:gold;
 s.DrawRectangle(860,876,200,9,pulse);

}
int main() {
 setvbuf(stdout,nullptr,_IONBF,0);
 std::puts("KAZUMA46: BOOT benchmark homebrew 2D, sem motor do jogo.");
 bool clock_ok=false, file_ok=false,dirs_ok=false;
 diagnostics(clock_ok,file_ok,dirs_ok);
 auto* scene=new Scene2D(1920,1080,4);
 if(!scene->Init(0x4000000,2)) {
   std::puts("KAZUMA46: VIDEO_INIT_FALHOU");return 2;
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
 uint32_t previous=0; bool connected=false,seen_x=false,heavy=false;
 PerfStats perf{};
 for(unsigned frame=0;;frame++) {
  if(pad>=0) {
   OrbisPadData d{};
   const int rc=scePadReadState(pad,&d);
   connected=rc>=0 && d.connected;
   const uint32_t curr=connected?d.buttons:0;
   const uint32_t newly=curr & ~previous;
   previous=curr;
   if(newly & ORBIS_PAD_BUTTON_CROSS) {
     seen_x=true;std::puts("KAZUMA46: BOTAO_X_RECEBIDO");
   }
   if(newly & ORBIS_PAD_BUTTON_SQUARE) diagnostics(clock_ok,file_ok,dirs_ok);
   if(newly & ORBIS_PAD_BUTTON_TRIANGLE) {
    heavy=!heavy;
    perf=PerfStats{};
    std::printf("KAZUMA46: MODO=%s\n", heavy?"CARGA":"NORMAL");
   }
  }
  const uint64_t frame_start=nx::plat::monotonic_ns();
  scene->SetActiveFrameBuffer(int(frame%2));
  paint(*scene,clock_ok,file_ok,dirs_ok,connected,seen_x,heavy,perf,frame);
  scene->SubmitFlip(int(frame));
  scene->FrameWait(int(frame));
  const uint64_t frame_end=nx::plat::monotonic_ns();
  if(frame_start>0 && frame_end>frame_start) record_frame(perf,frame_end-frame_start);
 }
}
