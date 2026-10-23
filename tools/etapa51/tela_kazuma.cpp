// Kazuma 51 — memoria virtual: microteste no processo deste homebrew.
// NUNCA mapeia com MAP_FIXED, nunca abre dados do jogo, nunca modifica saves.
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cerrno>
#include <sstream>
#include <string>
#include <sys/mman.h>
#include <unistd.h>
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

struct Probe {
 bool page_ok=false, hint_ok=false, reserve_ok=false, commit_ok=false, write_ok=false;
 bool decommit_called=false;
 int guest_bases_ok=0;
 unsigned guest_bases_tested=0;
 long page_bytes=0;
};
static Probe probe_once() {
 Probe r{};
 std::puts("KAZUMA51: INICIO TESTE ISOLADO - SEM JOGO");
 const long page=sysconf(_SC_PAGESIZE);
 r.page_bytes=page;
 // Limits conservative for isolated memory test. No assumptions about the game's virtual address layout.
 if (page<4096 || page>65536 || (static_cast<unsigned long>(page)&(static_cast<unsigned long>(page)-1))) {
  std::printf("KAZUMA51: PAGE_SIZE_INVALIDA=%ld\n",page);return r;
 }
 r.page_ok=true;
 std::printf("KAZUMA51: PAGE_SIZE=%ld\n",page);
 // Ask OS for one scratch page; unmap it; attempt to reserve exactly that same address.
 // Kernel may reallocate that address meanwhile; failure is safe and must be reported, not masked.
 void* scratch=mmap(nullptr,static_cast<size_t>(page),PROT_NONE,MAP_PRIVATE|MAP_ANON,-1,0);
 if (scratch == MAP_FAILED) {
  std::printf("KAZUMA51: HINT_MMAP=FALHA errno=%d\n",errno);return r;
 }
 const uintptr_t addr=reinterpret_cast<uintptr_t>(scratch);
 r.hint_ok=munmap(scratch,static_cast<size_t>(page))==0;
 if (!r.hint_ok) {std::puts("KAZUMA51: HINT_UNMAP=FALHA");return r;}
 r.reserve_ok=nx::plat::reserve(static_cast<uint64_t>(addr),static_cast<uint64_t>(page));
 std::printf("KAZUMA51: RESERVE=%s\n",r.reserve_ok?"OK":"RECUSADA_SEM_SOBRESCRITA");
 if (r.reserve_ok) {
  r.commit_ok=nx::plat::commit(static_cast<uint64_t>(addr),static_cast<uint64_t>(page));
  std::printf("KAZUMA51: COMMIT=%s\n",r.commit_ok?"OK":"FALHA");
  if (r.commit_ok) {
   volatile unsigned char* bytes=reinterpret_cast<volatile unsigned char*>(addr);
   bytes[0]=0x5A; bytes[static_cast<size_t>(page)-1]=0xA5;
   r.write_ok=bytes[0]==0x5A && bytes[static_cast<size_t>(page)-1]==0xA5;
   std::printf("KAZUMA51: READ_WRITE=%s\n",r.write_ok?"OK":"FALHA");
  }
  nx::plat::decommit(static_cast<uint64_t>(addr),static_cast<uint64_t>(page));
  r.decommit_called=true;  // void return: cannot claim success just from calling it.
  std::puts("KAZUMA51: DECOMMIT=CHAMADO_SEM_VERIFICACAO_DE_PROTECAO");
  // Never access this address after decommit.
  const int unmap_rc=munmap(reinterpret_cast<void*>(addr),static_cast<size_t>(page));
  std::printf("KAZUMA51: LIMPEZA_MUNMAP=%s\n",unmap_rc==0?"OK":"FALHA");
 }
 // Minimal one-page probes for three base addresses listed in the game's PUBLIC build manifest.
 // Not a test that complete AOT modules or assets will fit. Never MAP_FIXED or touch reserved memory.
 const uint64_t module_bases[3]={0x4000000000ULL,0x4010000000ULL,0x4020000000ULL};
 const char* names[3]={"MAIN","SDK","SUBSDK0"};
 for(unsigned i=0;i<3;i++) {
  if(module_bases[i]%static_cast<uint64_t>(page)!=0){
   std::printf("KAZUMA51: BASE_%s=DESALINHADA\n",names[i]);continue;
  }
  ++r.guest_bases_tested;
  const bool ok=nx::plat::reserve(module_bases[i],static_cast<uint64_t>(page));
  if(ok) {
   ++r.guest_bases_ok;
   (void)munmap(reinterpret_cast<void*>(static_cast<uintptr_t>(module_bases[i])),static_cast<size_t>(page));
  }
  std::printf("KAZUMA51: BASE_%s_PAGINA=%s\n",names[i],ok?"ACEITA":"RECUSADA");
 }
 std::printf("KAZUMA51: RESULTADO=PAGE_%s RESERVE_%s COMMIT_%s WRITE_%s BASES_%d_DE_%u\n",
   r.page_ok?"OK":"FALHA",r.reserve_ok?"OK":"FALHA",r.commit_ok?"OK":"FALHA",r.write_ok?"OK":"FALHA",
   r.guest_bases_ok,r.guest_bases_tested);
 std::puts("KAZUMA51: FIM TESTE ISOLADO - NAO VALIDOU BOOT CASTLEVANIA");
 return r;
}
static void paint(Scene2D& s,const Probe& r,bool pad,bool pressed,unsigned frame) {
 const Color bg={13,15,29}, panel={29,38,58}, gold={218,173,94},white={244,238,225};
 const Color green={80,220,155},red={230,94,105},muted={138,154,174};
 s.FrameBufferFill(bg);
 s.DrawRectangle(84,90,1752,8,gold);
 s.DrawRectangle(86,980,1748,5,gold);
 s.DrawRectangle(245,245,1430,665,panel);
 s.DrawRectangle(255,255,1410,645,bg);
 center(s,"KAZUMA PORT GAMES BR",136,4,gold);
 center(s,"MEMORIA PS4 - TESTE ISOLADO",290,4,white);
 center(s,r.page_ok?"PAGINA: OK":"PAGINA: FALHA",395,4,r.page_ok?green:red);
 center(s,r.reserve_ok?"RESERVA: OK":"RESERVA: RECUSADA",450,4,r.reserve_ok?green:red);
 center(s,r.commit_ok?"COMMIT: OK":"COMMIT: NAO VALIDADO",505,4,r.commit_ok?green:muted);
 center(s,r.write_ok?"LEITURA E ESCRITA: OK":"LEITURA E ESCRITA: NAO VALIDADO",560,3,r.write_ok?green:muted);
 center(s,r.decommit_called?"DECOMMIT: CHAMADO":"DECOMMIT: NAO CHAMADO",615,3,r.decommit_called?green:muted);
 char line[96];
 std::snprintf(line,sizeof(line),"BASES TESTADAS: %d DE %u",r.guest_bases_ok,r.guest_bases_tested);
 center(s,line,670,3,white);
 center(s,pad?"CONTROLE: CONECTADO":"CONTROLE: INDISPONIVEL",725,3,pad?green:muted);
 center(s,pressed?"X: RECEBIDO":"APERTE X PARA TESTAR",780,3,pressed?green:muted);
 center(s,"SO UMA PAGINA POR BASE - NAO E O JOGO",840,3,muted);
 center(s,"PS: SAIR - REGISTROS KAZUMA51 NO KLOG",930,3,white);
 s.DrawRectangle(860,876,200,9,(frame/40)%2?green:gold);
}
int main() {
 setvbuf(stdout,nullptr,_IONBF,0);
 std::puts("KAZUMA51: BOOT HOMEBREW - SONDA DE MEMORIA");
 const Probe probe=probe_once();
 auto* scene=new Scene2D(1920,1080,4);
 if(!scene->Init(0x4000000,2)) {std::puts("KAZUMA51: VIDEO_INIT_FALHOU");return 2;}
 bool pad_ready = scePadInit()==0;
 int pad=-1;
 if(pad_ready){
  OrbisUserServiceInitializeParams params{};
  params.priority=ORBIS_KERNEL_PRIO_FIFO_NORMAL;
  if(sceUserServiceInitialize(&params)==0){
   int user=-1;
   if(sceUserServiceGetInitialUser(&user)==0&&user>=0)
    pad=scePadOpen(user,ORBIS_PAD_PORT_TYPE_STANDARD,0,nullptr);
  }
 }
 bool connected=false,seen_x=false;
 uint32_t previous=0;
 for(unsigned frame=0;;frame++){
  if(pad>=0){
   OrbisPadData d{};
   const int rc=scePadReadState(pad,&d);
   connected=rc>=0&&d.connected;
   const uint32_t curr=connected?d.buttons:0;
   const uint32_t newly=curr&~previous;previous=curr;
   if(newly&ORBIS_PAD_BUTTON_CROSS){seen_x=true;std::puts("KAZUMA51: BOTAO_X_RECEBIDO");}
  }
  scene->SetActiveFrameBuffer(int(frame%2));
  paint(*scene,probe,connected,seen_x,frame);
  scene->SubmitFlip(int(frame));
  scene->FrameWait(int(frame));
 }
}
