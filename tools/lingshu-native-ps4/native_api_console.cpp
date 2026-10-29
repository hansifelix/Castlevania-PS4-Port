// Lingshu 190 - dedicated PS4 native memory API probe; NOT A GAME.
// Uses the SAME graphics helper as real stage 181, with no mmap giant tests.
// Calls the isolated and host-tested stage187 bridge one time and only logs
// what the PS4 API actually returned. Never claims boot or game play.
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <sstream>
#include <orbis/libkernel.h>
#include "graphics.h"
#include "log.h"

std::stringstream debugLogStream;
extern "C" bool lingshu187_native_probe(std::FILE* log);
namespace {
std::FILE* open_log(const char*& place) {
    constexpr const char* paths[]={
       "/data/lingshu190-native-virtual-range.log",
       "/user/data/lingshu190-native-virtual-range.log",
       "/mnt/usb0/lingshu190-native-virtual-range.log"
    };
    for(const char* path:paths){
        std::FILE* f=std::fopen(path,"w");
        if(f){place=path;return f;}
    }
    place="STDOUT_ONLY";
    return stdout;
}
// Small block-glyph font for status screen; not a game renderer.
struct Glyph {char c;unsigned char row[7];};
const Glyph font[]={
 {'A',{14,17,17,31,17,17,17}},{'B',{30,17,17,30,17,17,30}},
 {'C',{14,17,16,16,16,17,14}},{'D',{30,17,17,17,17,17,30}},
 {'E',{31,16,16,30,16,16,31}},{'F',{31,16,16,30,16,16,16}},
 {'G',{14,17,16,23,17,17,14}},{'H',{17,17,17,31,17,17,17}},
 {'I',{31,4,4,4,4,4,31}},{'J',{7,2,2,2,18,18,12}},
 {'K',{17,18,20,24,20,18,17}},{'L',{16,16,16,16,16,16,31}},
 {'M',{17,27,21,21,17,17,17}},{'N',{17,25,21,19,17,17,17}},
 {'O',{14,17,17,17,17,17,14}},{'P',{30,17,17,30,16,16,16}},
 {'Q',{14,17,17,17,21,18,13}},{'R',{30,17,17,30,20,18,17}},
 {'S',{15,16,16,14,1,1,30}},{'T',{31,4,4,4,4,4,4}},
 {'U',{17,17,17,17,17,17,14}},{'V',{17,17,17,17,17,10,4}},
 {'W',{17,17,17,21,21,21,10}},{'X',{17,17,10,4,10,17,17}},
 {'Y',{17,17,10,4,4,4,4}},{'Z',{31,1,2,4,8,16,31}},
 {'0',{14,17,19,21,25,17,14}},{'1',{4,12,4,4,4,4,14}},
 {'2',{14,17,1,2,4,8,31}},{'3',{30,1,1,14,1,1,30}},
 {'4',{2,6,10,18,31,2,2}},{'5',{31,16,30,1,1,17,14}},
 {'6',{6,8,16,30,17,17,14}},{'7',{31,1,2,4,8,8,8}},
 {'8',{14,17,17,14,17,17,14}},{'9',{14,17,17,15,1,2,12}},
 {'-',{0,0,0,31,0,0,0}},{':',{0,4,4,0,4,4,0}},
 {'/',{1,1,2,4,8,16,16}}
};
void draw(Scene2D& scene,const char* s,int x,int y,int scale,Color c) {
    for(;*s;++s,x+=6*scale)for(const auto& g:font)if(g.c==*s){
        for(int row=0;row<7;row++)for(int col=0;col<5;col++)
            if(g.row[row]&(1u<<(4-col)))
                scene.DrawRectangle(x+col*scale,y+row*scale,scale,scale,c);
        break;
    }
}
}
int main(){
    std::setvbuf(stdout,nullptr,_IONBF,0);
    const char* log_path=nullptr;
    std::FILE* log=open_log(log_path);
    std::fprintf(log,"LINGSHU190_START=SMALL_NATIVE_PS4_TEST_ONLY_NOT_GAME\n");
    std::fprintf(log,"LINGSHU190_LOG_PATH=%s\n",log_path);
    std::fprintf(log,"LINGSHU190_GUARDS=16KiB_1MiB_16MiB_ONLY_MANDATORY_CLEANUP_NO_MAP_FIXED\n");
    std::fflush(log);
    const bool fully_completed=lingshu187_native_probe(log);
    std::fprintf(log,"LINGSHU190_DIAGNOSTIC=%s\n",
        fully_completed?"COMPLETED_CHECK_SUMMARY_NOT_GAME_SUCCESS":
                        "STOPPED_UNSAFE_AFTER_NATIVE_RESPONSE");
    std::fflush(log);
    if(log!=stdout)std::fclose(log);

    auto* scene=new Scene2D(1920,1080,4);
    if(!scene->Init(0x4000000,2)){
        std::puts("LINGSHU190_VIDEO=FAILED_GET_LOG_BY_FTP");
        for(;;)sceKernelUsleep(1000000);
    }
    const Color bg{9,16,30},white{233,240,249},yellow{238,184,85};
    const Color red{236,92,92};
    for(int frame=0;;++frame) {
        scene->SetActiveFrameBuffer(frame&1);
        scene->FrameBufferFill(bg);
        draw(*scene,"LINGSHU 190 - API NATIVA PS4",90,95,5,white);
        draw(*scene,"DIAGNOSTICO DE MEMORIA SEM JOGO",95,240,4,yellow);
        draw(*scene,"RESERVAS PEQUENAS 16K 1M 16M",95,395,4,white);
        draw(*scene,fully_completed?"TESTE FINALIZADO VERIFIQUE LOG":
                             "TESTE INTERROMPIDO VERIFIQUE LOG",
             95,550,4,fully_completed?yellow:red);
        draw(*scene,"LOG PELO FTP NO PS4",95,720,4,white);
        draw(*scene,"BOTAO PS PARA SAIR",95,900,3,yellow);
        draw(*scene,"NAO PROVA QUE O CASTLEVANIA INICIA",95,980,3,white);
        scene->SubmitFlip(frame);
        scene->FrameWait(frame);
        sceKernelUsleep(50000);
    }
}
