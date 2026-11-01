// Lingshu 210: real read_at path + controlled pread interruption.
// No game/AOT/ROM bytes. The only mocked boundary is the POSIX syscall.
#include "platform.h"
#include <cerrno>
#include <climits>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <sys/types.h>
#include <unistd.h>

enum class Behavior { Real, Partial, HardError, Observe };
static Behavior behavior=Behavior::Real;
static int calls=0;
static bool offsets_match=true;
extern "C" ssize_t __real_pread(int, void*, size_t, off_t);

extern "C" ssize_t __wrap_pread(int fd, void* dest, size_t count, off_t offset) {
    ++calls;
    if (behavior==Behavior::Partial) {
        const off_t offsets[]={7,9,9,12};
        if (calls>4 || offset!=offsets[calls-1]) offsets_match=false;
        if (calls==1) {
            if (count<2) return -1;
            std::memcpy(dest,"HE",2);
            return 2;
        }
        if (calls==2) { errno=EINTR; return -1; }
        if (calls==3) {
            if (count<3) return -1;
            std::memcpy(dest,"LLO",3);
            return 3;
        }
        return 0;  // EOF after five bytes
    }
    if (behavior==Behavior::HardError) { errno=EIO; return -1; }
    if (behavior==Behavior::Observe) { errno=EINVAL; return -1; }
    return __real_pread(fd,dest,count,offset);
}

#define CHECK(expr) do { if (!(expr)) { \
    std::fprintf(stderr,"LINGSHU210_READ_AT_FAILED line=%d: %s\n",__LINE__,#expr); \
    return 1; } } while (0)

int main() {
    FILE* f=std::tmpfile();
    CHECK(f!=nullptr);
    constexpr char data[]="abcdefghij";
    CHECK(std::fwrite(data,1,sizeof(data)-1,f)==sizeof(data)-1);
    CHECK(std::fflush(f)==0);
    char out[16]={};
    int tests=0;

    calls=0;
    CHECK(nx::plat::read_at(f,3,out,4)==4); ++tests;
    CHECK(std::memcmp(out,"defg",4)==0 && calls>=1); ++tests;
    CHECK(std::ftell(f)==10); ++tests;  // pread must not move file cursor
    CHECK(nx::plat::read_at(f,9,out,4)==1 && out[0]=='j'); ++tests;

    behavior=Behavior::Observe;
    calls=0;
    CHECK(nx::plat::read_at(nullptr,0,out,1)==0 && calls==0); ++tests;
    CHECK(nx::plat::read_at(f,0,nullptr,1)==0 && calls==0); ++tests;
    CHECK(nx::plat::read_at(f,-1,out,1)==0 && calls==0); ++tests;
    CHECK(nx::plat::read_at(f,0,out,0)==0 && calls==0); ++tests;
    CHECK(nx::plat::read_at(f,0,out,uint64_t(SSIZE_MAX)+1)==0 && calls==0); ++tests;
    // Before this patch the adapter issued pread with an impossible span.
    const auto max_off=std::numeric_limits<off_t>::max();
    CHECK(max_off>3);
    CHECK(nx::plat::read_at(f,static_cast<int64_t>(max_off-1),out,3)==0 && calls==0); ++tests;
    CHECK(nx::plat::read_at(f,static_cast<int64_t>(max_off),out,2)==0 && calls==0); ++tests;

    behavior=Behavior::Partial;
    calls=0;
    std::memset(out,0,sizeof(out));
    CHECK(nx::plat::read_at(f,7,out,7)==5); ++tests;
    CHECK(std::memcmp(out,"HELLO",5)==0 && calls==4 && offsets_match); ++tests;

    behavior=Behavior::HardError;
    calls=0;
    CHECK(nx::plat::read_at(f,0,out,3)==0 && calls==1); ++tests;

    CHECK(std::fclose(f)==0);
    std::printf("LINGSHU210_READ_AT_REGRESSION=PASSED_%d_CASES_LINUX_HOST_ONLY\n",tests);
    return 0;
}
