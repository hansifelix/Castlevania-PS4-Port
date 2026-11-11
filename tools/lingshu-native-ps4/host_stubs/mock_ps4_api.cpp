// Deterministic Linux fake of the Orbis native reservation ABI.
// Never calls real console API, maps a guest VA, or touches proprietary data.
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
namespace {
const char* mode(){
    const char* m=std::getenv("LINGSHU190_MOCK_MODE");
    return m?m:"success";
}
}
extern "C" std::int32_t sceKernelReserveVirtualRange(
        void** p,std::size_t bytes,std::int32_t flags,std::size_t align) {
    assert(p && flags==0 && align==0x4000);
    assert(bytes==0x4000 || bytes==1048576 || bytes==16777216);
    if(std::strcmp(mode(),"deny")==0) return -7;
    return 0;
}
extern "C" std::int32_t sceKernelMunmap(void* p,std::size_t n){
    assert(p && n>=0x4000);
    if(std::strcmp(mode(),"cleanup_fail")==0) return -9;
    return 0;
}
extern "C" int sceKernelUsleep(unsigned){return 0;}
