// Teste local apenas: nao declara compatibilidade PS4.
#include <cassert>
#include <cstdint>
#include <cstdlib>
#include <string>
namespace nx::plat {
bool headless();
uint64_t memguard_overlap_ns(uint64_t,uint64_t);
bool profile(const int64_t*, const uint64_t* const*, size_t,int,const std::string&);
std::string setting(const std::string&);
std::string data_root();
}
int main() {
    assert(!nx::plat::headless());
    assert(nx::plat::memguard_overlap_ns(5,10)==0);
    assert(!nx::plat::profile(nullptr,nullptr,0,1,"/tmp/no.txt"));
    assert(nx::plat::setting("kazuma_test_foo").empty());
    assert(nx::plat::setting("kazuma-test").empty());
    assert(nx::plat::data_root()=="/app0");
    setenv("NX_KAZUMA_TEST_FOO","ok",1);
    assert(nx::plat::setting("kazuma_test_foo")=="ok");
    setenv("NX_DATA_ROOT","/private/kazuma",1);
    assert(nx::plat::data_root()=="/private/kazuma");
    setenv("NX_DATA_ROOT","relative",1);
    assert(nx::plat::data_root()=="/app0");
    return 0;
}
