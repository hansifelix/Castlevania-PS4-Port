#include <nx/runtime.h>
#include "castlevania_resolution.hpp"
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>
#include <string_view>

void nx_castlevania_supported_resolutions(nx::CPU&, void (*)(nx::CPU&));
void nx_castlevania_fullscreen_mode(nx::CPU&, void (*)(nx::CPU&));
void nx_castlevania_fullscreen(nx::CPU&, void (*)(nx::CPU&));

namespace {
using Bytes=std::array<uint8_t,384>;
alignas(8) Bytes managed{};
unsigned originals=0,allocations=0;
uint64_t ptr(Bytes& b) {return reinterpret_cast<uint64_t>(b.data());}
template<class T> void put(uint64_t a,T value) {std::memcpy(reinterpret_cast<void*>(a),&value,sizeof(T));}
template<class T> T get(uint64_t a) {T v{};std::memcpy(&v,reinterpret_cast<const void*>(a),sizeof(T));return v;}
void original(nx::CPU&) {++originals;}
void setup_option(Bytes& item,uint32_t idx) {put<uint32_t>(ptr(item)+0x20,idx);}
}
namespace nx {
uint64_t test_video_static_usage=0;
void call(CPU& c,uint64_t target) {
    assert(target == NX_BASE+0x418f160ull);
    ++allocations;
    const uint64_t len=c.x[0];
    assert(len<64 && c.x[1]==0);
    managed.fill(0);
    put<int32_t>(ptr(managed)+16,static_cast<int32_t>(len));
    c.x[0]=ptr(managed);
}
[[noreturn]] void fatal(const char* msg, ...) {throw std::runtime_error(msg);}
[[noreturn]] void unimpl(CPU&,uint64_t,const char* msg) {throw std::runtime_error(msg);}
void log(const char*,...) {}
}
int main() {
    using namespace kazuma::ps4::video;
    nx::CPU cpu{};
    bool denied=false;
    try {nx_castlevania_supported_resolutions(cpu,nullptr);}
    catch(const std::runtime_error& e){denied=std::string(e.what()).find("original")!=std::string::npos;}
    assert(denied && originals==0);
    nx_castlevania_fullscreen(cpu,nullptr);
    assert(cpu.x[0]==0);
    denied=false;
    try {nx_castlevania_fullscreen_mode(cpu,nullptr);}
    catch(const std::runtime_error& e){denied=std::string(e.what()).find("VideoOut")!=std::string::npos;}
    assert(denied);

    alignas(8) Bytes self{},usage{},klass{},fields{},res_setting{},win_setting{},
        res_modes{},res_choices{},win_modes{},win_choices{},r0{},r1{},r2{},w0{},w1{},w2{},w3{};
    nx::test_video_static_usage=ptr(usage);
    put<uint64_t>(ptr(usage),ptr(klass));
    put<uint64_t>(ptr(klass)+0xb8,ptr(fields));
    put<uint64_t>(ptr(fields),ptr(res_modes));
    put<uint64_t>(ptr(fields)+0x10,ptr(win_modes));
    put<uint64_t>(ptr(self)+0x68,ptr(res_setting));
    put<uint64_t>(ptr(self)+0x58,ptr(win_setting));
    put<uint64_t>(ptr(res_setting)+0x58,ptr(res_choices));
    put<uint64_t>(ptr(win_setting)+0x58,ptr(win_choices));

    put<uint32_t>(ptr(res_modes)+24,3);
    put<uint32_t>(ptr(res_choices)+24,3);
    for(unsigned i=0;i<3;++i) {
        const uint32_t sizes[3][2]={{640,360},{1280,720},{1920,1080}};
        put<uint32_t>(ptr(res_modes)+32+i*8,sizes[i][0]);
        put<uint32_t>(ptr(res_modes)+36+i*8,sizes[i][1]);
    }
    setup_option(r0,0);setup_option(r1,1);setup_option(r2,2);
    put<uint64_t>(ptr(res_choices)+32,ptr(r0));
    put<uint64_t>(ptr(res_choices)+40,ptr(r1));
    put<uint64_t>(ptr(res_choices)+48,ptr(r2));
    put<uint32_t>(ptr(win_modes)+24,4);
    put<uint32_t>(ptr(win_choices)+24,4);
    Bytes* windows[]={&w0,&w1,&w2,&w3};
    for(unsigned i=0;i<4;++i) {
        setup_option(*windows[i],i);
        put<uint32_t>(ptr(win_modes)+32+i*4,i);
        put<uint64_t>(ptr(win_choices)+32+i*8,ptr(*windows[i]));
    }
    cpu.x[0]=ptr(self);
    denied=false;
    try{nx_castlevania_supported_resolutions(cpu,original);}
    catch(const std::runtime_error& e){denied=std::string(e.what()).find("VideoOut")!=std::string::npos;}
    assert(denied && originals==1 && allocations==0);
    assert(configure_native(1920,1080));
    assert(select_render(1280,720));
    nx_castlevania_supported_resolutions(cpu,original);
    assert(originals==2 && allocations==1);
    assert(get<uint32_t>(ptr(res_setting)+0x1c)==1);
    assert(get<uint8_t>(ptr(r0)+0x28)==1);
    assert(get<uint8_t>(ptr(r1)+0x28)==1);
    assert(get<uint8_t>(ptr(r2)+0x28)==1);
    assert(get<uint8_t>(ptr(w0)+0x28)==0);
    assert(get<uint8_t>(ptr(w1)+0x28)==1);
    assert(get<uint8_t>(ptr(w2)+0x28)==0);
    assert(get<uint8_t>(ptr(w3)+0x28)==0);
    assert(get<uint32_t>(ptr(win_setting)+0x1c)==1);
    assert(get<uint64_t>(ptr(r2)+0x10)==ptr(managed));
    assert(get<int32_t>(ptr(managed)+16)==9);
    const char16_t expected[]=u"1920x1080";
    for(unsigned i=0;i<9;++i)assert(get<char16_t>(ptr(managed)+20+2*i)==expected[i]);

    nx_castlevania_supported_resolutions(cpu,original);
    assert(originals==3 && allocations==1); // Reuse existing managed String.

    put<uint32_t>(ptr(res_modes)+32+8,640);
    put<uint32_t>(ptr(res_modes)+36+8,360);
    nx_castlevania_supported_resolutions(cpu,original);
    assert(get<uint8_t>(ptr(r0)+0x28)==1);
    assert(get<uint8_t>(ptr(r1)+0x28)==0); // Duplicate resolution rejected.

    put<uint32_t>(ptr(res_choices)+24,33);
    put<uint8_t>(ptr(r0)+0x28,77);
    nx_castlevania_supported_resolutions(cpu,original);
    assert(get<uint8_t>(ptr(r0)+0x28)==77); // Malformed size: no overwrite.

    nx_castlevania_fullscreen_mode(cpu,nullptr);
    assert(cpu.x[0]==1);
    nx_castlevania_fullscreen(cpu,nullptr);
    assert(cpu.x[0]==1);
}
