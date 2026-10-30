#include "concurrent_policy.h"
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

namespace {
enum class Mode { AllExact, DenyThird, RelocateThird, CleanupFail,
                  ErrorChangedThird, NullThird };
Mode mode=Mode::AllExact;
unsigned calls=0;
std::vector<std::uintptr_t> releases;
std::uintptr_t kThird=lingshu206::kRegions[2].address;
void reset(Mode m) { mode=m;calls=0;releases.clear(); }
std::int32_t reserve_mock(void** target,std::size_t bytes,std::int32_t flags,std::size_t align) {
    assert(target!=nullptr);
    assert(bytes==lingshu206::kBytes);
    assert(flags==0 && align==lingshu206::kPS4Page);
    assert(calls<lingshu206::kCount);
    assert(reinterpret_cast<std::uintptr_t>(*target)==lingshu206::kRegions[calls].address);
    ++calls;
    if(calls==3) {
        if(mode==Mode::DenyThird) return -7;
        if(mode==Mode::ErrorChangedThird) {
            *target=reinterpret_cast<void*>(kThird+lingshu206::kBytes);
            return -7;
        }
        if(mode==Mode::RelocateThird) {
            *target=reinterpret_cast<void*>(kThird+lingshu206::kBytes);
            return 0;
        }
        if(mode==Mode::NullThird) { *target=nullptr;return 0; }
    }
    return 0;
}
std::int32_t release_mock(void* addr,std::size_t bytes) {
    assert(bytes==lingshu206::kBytes);
    releases.push_back(reinterpret_cast<std::uintptr_t>(addr));
    if(mode==Mode::CleanupFail && releases.size()==1) return -9;
    return 0;
}
std::string take_log(std::FILE* f) {
    assert(std::fflush(f)==0);
    std::rewind(f);
    std::string data;
    char b[1024];
    while(std::size_t n=std::fread(b,1,sizeof b,f)) data.append(b,n);
    return data;
}
struct Run { lingshu206::Outcome out; std::string log; };
Run checked_run() {
    std::FILE* f=std::tmpfile();
    assert(f);
    auto result=lingshu206::run(f,reserve_mock,release_mock);
    auto log=take_log(f);
    assert(std::fclose(f)==0);
    return {result,log};
}
}
int main() {
    static_assert(lingshu206::kCount==5 && lingshu206::kBytes==16777216);
    reset(Mode::AllExact);
    auto ok=checked_run();
    assert(ok.out.all_five_coexisted && ok.out.fully_released);
    assert(ok.out.attempts==5 && ok.out.exact==5 && ok.out.released==5);
    assert(releases.size()==5);
    for(unsigned i=0;i<5;++i)
      assert(releases[i]==lingshu206::kRegions[4-i].address);
    assert(ok.log.find("LINGSHU206_ALL_FIVE=COEXISTED_16M_EACH")!=std::string::npos);
    assert(ok.log.find("LINGSHU206_FINAL=FIVE_16M_SIMULTANEOUS_EXACT_AND_RELEASED_NOT_GAME")!=std::string::npos);
    std::puts("LINGSHU206_FIVE_HELD_REVERSE_RELEASE=PASS_MOCK");

    reset(Mode::DenyThird);
    auto denied=checked_run();
    assert(!denied.out.all_five_coexisted && denied.out.fully_released);
    assert(denied.out.attempts==3 && denied.out.denied==1 && denied.out.released==2);
    assert(releases.size()==2);
    assert(releases[0]==lingshu206::kRegions[1].address &&
           releases[1]==lingshu206::kRegions[0].address);
    assert(denied.log.find("LINGSHU206_FINAL=INCOMPLETE_BUT_CLEAN_NOT_GAME")!=std::string::npos);
    std::puts("LINGSHU206_DENIAL_ROLLBACK=PASS_MOCK");

    reset(Mode::RelocateThird);
    auto shifted=checked_run();
    assert(!shifted.out.all_five_coexisted && shifted.out.fully_released);
    assert(shifted.out.attempts==3 && shifted.out.relocated==1 && shifted.out.released==3);
    assert(releases.size()==3 && releases[0]==kThird+lingshu206::kBytes);
    assert(releases[1]==lingshu206::kRegions[1].address &&
           releases[2]==lingshu206::kRegions[0].address);
    std::puts("LINGSHU206_RELOCATION_RELEASES_ACTUAL_AND_ROLLBACK=PASS_MOCK");

    reset(Mode::CleanupFail);
    auto failure=checked_run();
    assert(failure.out.all_five_coexisted);
    assert(!failure.out.fully_released && !failure.out.safe_to_continue);
    assert(failure.out.release_failed==1 && releases.size()==5);
    assert(failure.log.find("LINGSHU206_FINAL=STOPPED_UNSAFE_NOT_GAME")!=std::string::npos);
    std::puts("LINGSHU206_CLEANUP_FAILURE_UNSAFE=PASS_MOCK");

    reset(Mode::ErrorChangedThird);
    auto changed=checked_run();
    assert(!changed.out.safe_to_continue && changed.out.unsafe==1);
    assert(changed.out.attempts==3 && releases.size()==2);
    assert(changed.log.find("status=ERROR_CHANGED_PTR")!=std::string::npos);
    std::puts("LINGSHU206_ERROR_CHANGED_POINTER_STOP=PASS_MOCK");

    reset(Mode::NullThird);
    auto anomalous=checked_run();
    assert(!anomalous.out.safe_to_continue && anomalous.out.unsafe==1);
    assert(anomalous.out.attempts==3 && releases.size()==2);
    assert(anomalous.log.find("status=ANOMALOUS_PTR")!=std::string::npos);
    std::puts("LINGSHU206_NULL_SUCCESS_STOP=PASS_MOCK");
    std::puts("LINGSHU206_HOST_SUITE=PASS_LINUX_MOCK_NOT_PS4");
}
