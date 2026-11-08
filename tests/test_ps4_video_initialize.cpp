#include <nx/runtime.h>
#include "castlevania_resolution.hpp"
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>

void nx_castlevania_video_initialize(nx::CPU&, void (*)(nx::CPU&));
void nx_castlevania_set_fullscreen_mode(nx::CPU&, void (*)(nx::CPU&));

namespace {
using Memory = std::array<uint8_t,768>;
template<class T> void put(uint64_t a, T value) {
    std::memcpy(reinterpret_cast<void*>(a), &value, sizeof(T));
}
template<class T> T get(uint64_t a) {
    T v{};std::memcpy(&v,reinterpret_cast<const void*>(a),sizeof(T));return v;
}
uint64_t at(Memory& m) {return reinterpret_cast<uint64_t>(m.data());}
constexpr uint64_t kGetter=0x33330000ull;
constexpr uint64_t kValidator=0x44440000ull;
unsigned getter_calls=0,validator_calls=0,initialize_calls=0,set_calls=0;
uint64_t resolution_setting=0,window_setting=0;
void setter_original(nx::CPU& c) {++set_calls; assert(c.x[0]==1);}
void initialize_original(nx::CPU& c) {
    ++initialize_calls;
    assert(c.x[0]!=0);
    const unsigned prior_set_calls=set_calls;
    nx::CPU nested{};
    nested.x[0]=0;
    nx_castlevania_set_fullscreen_mode(nested, setter_original);
    assert(set_calls==prior_set_calls); // No extra setter call during initialization.
}
}
namespace nx {
uint64_t test_video_static_usage=0;
void call(CPU& c, uint64_t target) {
    if (target==kGetter) {
        ++getter_calls;
        assert(c.x[1]==0x123456);
        assert(c.x[0]==window_setting);
        c.x[0]=0; // The original selection matches default 0.
        return;
    }
    if (target==kValidator) {
        ++validator_calls;
        assert(c.x[0]==resolution_setting || c.x[0]==window_setting);
        assert(c.x[1]==1 && c.x[2]==0x777);
        return;
    }
    throw std::logic_error("unexpected guest call");
}
[[noreturn]] void fatal(const char* msg, ...) {throw std::runtime_error(msg);}
[[noreturn]] void unimpl(CPU&, uint64_t, const char* msg) {throw std::runtime_error(msg);}
void log(const char*, ...) {}
}
int main() {
    using namespace kazuma::ps4::video;
    nx::CPU c{};
    bool denied=false;
    try {nx_castlevania_video_initialize(c,nullptr);}
    catch(const std::runtime_error& e) {
        denied=std::string(e.what()).find("original")!=std::string::npos;
    }
    assert(denied && initialize_calls==0);
    denied=false;
    try {nx_castlevania_video_initialize(c,initialize_original);}
    catch(const std::runtime_error& e) {
        denied=std::string(e.what()).find("VideoOut")!=std::string::npos;
    }
    assert(denied && initialize_calls==0);
    denied=false;
    try {nx_castlevania_set_fullscreen_mode(c,setter_original);}
    catch(const std::runtime_error& e) {
        denied=std::string(e.what()).find("VideoOut")!=std::string::npos;
    }
    assert(denied && set_calls==0);

    alignas(8) Memory self{},usage{},static_klass{},fields{},res_setting{},win_setting{},
        setting_klass{},res_modes{},res_choices{},win_modes{},win_choices{},r0{},
        w0{},w1{},w2{},w3{},native_label{};
    nx::test_video_static_usage=at(usage);
    put(at(usage),at(static_klass));
    put(at(static_klass)+0xb8,at(fields));
    put(at(fields),at(res_modes));
    put(at(fields)+0x10,at(win_modes));
    put(at(self)+0x68,at(res_setting));
    put(at(self)+0x58,at(win_setting));
    resolution_setting=at(res_setting);
    window_setting=at(win_setting);
    put(at(res_setting),at(setting_klass));
    put(at(win_setting),at(setting_klass));
    put(at(setting_klass)+0x198,kGetter);
    put(at(setting_klass)+0x1a0,uint64_t(0x123456));
    put(at(setting_klass)+0x188,kValidator);
    put(at(setting_klass)+0x190,uint64_t(0x777));
    put(at(res_setting)+0x58,at(res_choices));
    put(at(win_setting)+0x58,at(win_choices));
    put<uint32_t>(at(res_modes)+24,1);
    put<uint32_t>(at(res_modes)+32,1920);
    put<uint32_t>(at(res_modes)+36,1080);
    put<uint32_t>(at(res_choices)+24,1);
    put<uint64_t>(at(res_choices)+32,at(r0));
    put<uint32_t>(at(r0)+0x20,0);
    const char16_t native[]=u"1920x1080";
    put<int32_t>(at(native_label)+16,9);
    std::memcpy(reinterpret_cast<void*>(at(native_label)+20),native,9*sizeof(char16_t));
    put<uint64_t>(at(r0)+0x10,at(native_label));
    put<uint32_t>(at(win_modes)+24,4);
    put<uint32_t>(at(win_choices)+24,4);
    Memory* windows[]={&w0,&w1,&w2,&w3};
    for(unsigned i=0;i<4;++i) {
        put<uint32_t>(at(*windows[i])+0x20,i);
        put<uint32_t>(at(win_modes)+32+i*4,i);
        put<uint64_t>(at(win_choices)+32+i*8,at(*windows[i]));
    }
    c.x[0]=at(self);
    assert(configure_native(1920,1080));
    nx_castlevania_video_initialize(c,initialize_original);
    assert(initialize_calls==1 && set_calls==0);
    assert(validator_calls==2 && getter_calls==1);
    assert(get<uint32_t>(at(res_setting)+0x1c)==0);
    assert(get<uint32_t>(at(win_setting)+0x18)==1);
    assert(get<uint32_t>(at(win_setting)+0x1c)==1);
    assert(get<uint8_t>(at(w1)+0x28)==1);
    assert(get<uint8_t>(at(w0)+0x28)==0);
    assert(get<uint64_t>(at(r0)+0x10)==at(native_label));

    nx::CPU setter{};
    setter.x[0]=0;
    nx_castlevania_set_fullscreen_mode(setter,setter_original);
    assert(set_calls==1 && setter.x[0]==1);
    setter.x[0]=3;
    nx_castlevania_set_fullscreen_mode(setter,setter_original);
    assert(set_calls==2 && setter.x[0]==1);
    denied=false;
    try {nx_castlevania_set_fullscreen_mode(setter,nullptr);}
    catch(const std::runtime_error& e) {
        denied=std::string(e.what()).find("original")!=std::string::npos;
    }
    assert(denied && set_calls==2);

    // Wrong mode list must fail rather than invent a fullscreen setting.
    put<uint32_t>(at(win_modes)+36,0);
    put<uint32_t>(at(win_setting)+0x18,0); // Exercise the default-match path.
    denied=false;
    try {nx_castlevania_video_initialize(c,initialize_original);}
    catch(const std::runtime_error& e) {
        denied=std::string(e.what()).find("fullscreen mode missing")!=std::string::npos;
    }
    assert(denied && initialize_calls==2);
    // After failure the thread_local initialization guard is reset.
    setter.x[0]=0;
    nx_castlevania_set_fullscreen_mode(setter,setter_original);
    assert(set_calls==3);
}
