#pragma once
// Synthetic host test fixture. Real PS4 compilation uses pinned nx/cpu.h and nx/runtime.h.
#include <nx/cpu.h>
#include <cstdint>
#include <cstring>
namespace nx {
extern uint64_t test_video_static_usage;
template<class T> inline T ld(uint64_t addr) {
    if(addr==NX_BASE+0x6be3ec8ull) addr=reinterpret_cast<uint64_t>(&test_video_static_usage);
    T out{}; std::memcpy(&out,reinterpret_cast<const void*>(addr),sizeof(T)); return out;
}
template<class T> inline void st(uint64_t addr,T val) {
    std::memcpy(reinterpret_cast<void*>(addr),&val,sizeof(T));
}
void call(CPU&,uint64_t);
[[noreturn]] void fatal(const char*,...);
void log(const char*,...);
}
