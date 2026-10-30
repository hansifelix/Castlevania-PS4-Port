#include "flexible_policy.h"
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
namespace {
alignas(0x4000) unsigned char page[lingshu207::kPage];
enum class Mode { Success, Denied, ErrorChanged, NullSuccess,
                  Misaligned, ProtectReadDenied, ProtectRWDenied, UnmapDenied };
Mode mode=Mode::Success;
unsigned maps=0,protects=0,unmaps=0;
void reset(Mode m) {mode=m;maps=protects=unmaps=0;std::memset(page,0,sizeof page);}
std::int32_t map_mock(void** p,std::size_t n,std::int32_t prot,std::int32_t flags) {
    assert(p && !*p && n==lingshu207::kPage);
    assert(prot==3 && flags==0);
    ++maps;
    if(mode==Mode::Denied)return -7;
    *p=page;
    if(mode==Mode::ErrorChanged)return -7;
    if(mode==Mode::NullSuccess){*p=nullptr;return 0;}
    if(mode==Mode::Misaligned){*p=page+1;return 0;}
    return 0;
}
std::int32_t protect_mock(const void* p,std::size_t n,std::int32_t prot) {
    assert(p==page && n==lingshu207::kPage);
    assert(prot==1 || prot==3);
    ++protects;
    if(mode==Mode::ProtectReadDenied && prot==1)return -8;
    if(mode==Mode::ProtectRWDenied && prot==3)return -9;
    return 0;
}
std::int32_t unmap_mock(void* p,std::size_t n) {
    assert(p==page && n==lingshu207::kPage);
    ++unmaps;
    return mode==Mode::UnmapDenied?-10:0;
}
struct Attempt {lingshu207::Result result;std::string log;};
Attempt run_test() {
    std::FILE* f=std::tmpfile();
    assert(f);
    auto r=lingshu207::run(f,map_mock,protect_mock,unmap_mock);
    assert(std::fflush(f)==0);
    std::rewind(f);
    std::string log;
    char b[512];
    while(std::size_t n=std::fread(b,1,sizeof b,f))log.append(b,n);
    assert(std::fclose(f)==0);
    return {r,log};
}
}
int main() {
    reset(Mode::Success);
    auto ok=run_test();
    assert(ok.result.complete && ok.result.mapped && ok.result.cleanup_ok);
    assert(ok.result.bytes_verified && ok.result.readonly_verified && ok.result.rw_restored);
    assert(page[0]==0xA5 && page[lingshu207::kPage-1]==0x5A);
    assert(maps==1 && protects==2 && unmaps==1);
    assert(ok.log.find("LINGSHU207_FINAL=FLEXIBLE_16K_RW_RO_RW_AND_CLEANUP_OK_NOT_GAME")!=std::string::npos);
    std::puts("LINGSHU207_FLEXIBLE_RW_RO_RW=PASS_LINUX_MOCK");

    reset(Mode::Denied);
    auto d=run_test();
    assert(!d.result.complete && !d.result.unsafe && !d.result.mapped && maps==1 && protects==0 && unmaps==0);
    std::puts("LINGSHU207_MAP_DENIED=PASS_LINUX_MOCK");

    reset(Mode::ErrorChanged);
    auto e=run_test();
    assert(e.result.unsafe && maps==1 && protects==0 && unmaps==0);
    std::puts("LINGSHU207_ERROR_CHANGED_OUTPUT=PASS_LINUX_MOCK");

    reset(Mode::NullSuccess);
    auto n=run_test();
    assert(n.result.unsafe && maps==1 && protects==0 && unmaps==0);
    std::puts("LINGSHU207_NULL_SUCCESS=PASS_LINUX_MOCK");

    reset(Mode::Misaligned);
    auto m=run_test();
    assert(m.result.unsafe && maps==1 && protects==0 && unmaps==0);
    std::puts("LINGSHU207_MISALIGNED_SUCCESS=PASS_LINUX_MOCK");

    reset(Mode::ProtectReadDenied);
    auto readfail=run_test();
    assert(!readfail.result.complete && !readfail.result.unsafe && readfail.result.cleanup_ok);
    assert(readfail.result.bytes_verified && protects==1 && unmaps==1);
    std::puts("LINGSHU207_READ_PROTECTION_DENIED_CLEANUP=PASS_LINUX_MOCK");

    reset(Mode::ProtectRWDenied);
    auto rwfail=run_test();
    assert(!rwfail.result.complete && !rwfail.result.unsafe && rwfail.result.cleanup_ok);
    assert(rwfail.result.readonly_verified && !rwfail.result.rw_restored);
    assert(protects==2 && unmaps==1);
    std::puts("LINGSHU207_RESTORE_PROTECTION_DENIED_CLEANUP=PASS_LINUX_MOCK");

    reset(Mode::UnmapDenied);
    auto u=run_test();
    assert(!u.result.complete && u.result.unsafe && u.result.cleanup_attempted && !u.result.cleanup_ok);
    assert(maps==1 && protects==2 && unmaps==1);
    std::puts("LINGSHU207_UNMAP_FAILED_UNSAFE=PASS_LINUX_MOCK");
    std::puts("LINGSHU207_HOST_SUITE=PASS_LINUX_MOCK_NOT_PS4");
}
