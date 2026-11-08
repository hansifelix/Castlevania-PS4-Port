#include <nx/runtime.h>
#include "castlevania_resolution.hpp"
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>

void nx_castlevania_resolution_changed(nx::CPU&, void (*)(nx::CPU&));

namespace nx {
uint64_t test_static_usage_pointer = 0;
namespace test {
uint64_t selector_method = 0x1234beefull;
int selected_index = 1;
int selection_calls = 0, resolution_calls = 0, originals = 0;
uint64_t last_selected_self = 0, last_selected_arg = 0;
uint32_t width = 0, height = 0;
uint64_t mode = 0;
}
void call(CPU& c, uint64_t target) {
    if (target == test::selector_method) {
        ++test::selection_calls;
        test::last_selected_self = c.x[0];
        test::last_selected_arg = c.x[1];
        c.x[0] = static_cast<uint64_t>(test::selected_index);
        return;
    }
    if (target == NX_BASE + 0x4e00a50ull) {
        ++test::resolution_calls;
        test::width = static_cast<uint32_t>(c.x[0]);
        test::height = static_cast<uint32_t>(c.x[1]);
        test::mode = c.x[2];
        assert(c.x[3] == 0x100000000ull && c.x[4] == 0);
        return;
    }
    throw std::logic_error("unexpected guest function");
}
[[noreturn]] void fatal(const char* message, ...) { throw std::runtime_error(message); }
[[noreturn]] void unimpl(CPU&, uint64_t, const char* message) { throw std::runtime_error(message); }
void log(const char*, ...) {}
}
namespace {
using Memory = std::array<uint8_t, 640>;
template<class T> void put(uint64_t address, T value) {
    std::memcpy(reinterpret_cast<void*>(address), &value, sizeof(T));
}
uint64_t at(Memory& m) { return reinterpret_cast<uint64_t>(m.data()); }
void original(nx::CPU& c) {
    ++nx::test::originals;
    // Should never replace the original guest receiver with a fake one.
    assert(c.x[0] != 0);
}
void expect_render(uint32_t w, uint32_t h) {
    uint32_t actual_w=0, actual_h=0;
    kazuma::ps4::video::render_size(actual_w, actual_h);
    assert(actual_w==w && actual_h==h);
}
}
int main() {
    using namespace nx::test;
    using namespace kazuma::ps4::video;
    Memory receiver{}, setting{}, klass{}, usage{}, static_klass{}, fields{}, choices{};
    put(at(receiver)+0x68, at(setting));
    put(at(setting), at(klass));
    put(at(klass)+0x198, selector_method);
    put(at(klass)+0x1a0, uint64_t(0x55));
    nx::test_static_usage_pointer=at(usage);
    put(at(usage), at(static_klass));
    put(at(static_klass)+0xb8, at(fields));
    put(at(fields), at(choices));
    put(at(choices)+24, uint32_t(3));
    put(at(choices)+32, uint32_t(1920));
    put(at(choices)+36, uint32_t(1080));
    put(at(choices)+40, uint32_t(1280));
    put(at(choices)+44, uint32_t(720));
    put(at(choices)+48, uint32_t(800));
    put(at(choices)+52, uint32_t(600));
    nx::CPU c{};
    c.x[0]=at(receiver);

    bool denied=false;
    try { nx_castlevania_resolution_changed(c, nullptr); }
    catch (const std::runtime_error& e) {
        denied=std::string(e.what()).find("original")!=std::string::npos;
    }
    assert(denied && originals==0 && selection_calls==0);

    // No valid VideoOut: original and selected run, but guest screen setter does not.
    nx_castlevania_resolution_changed(c, original);
    assert(originals==1 && selection_calls==1 && resolution_calls==0);
    assert(last_selected_self==at(setting) && last_selected_arg==0x55);
    assert(!ready());

    assert(configure_native(1920,1080));
    nx_castlevania_resolution_changed(c, original);
    assert(originals==2 && selection_calls==2 && resolution_calls==1);
    assert(width==1280 && height==720 && mode==1);
    expect_render(1280,720);
    uint32_t nw=0, nh=0;
    native_size(nw,nh);
    assert(nw==1920 && nh==1080); // Never resize physical PS4 output.

    selected_index=2; // 800x600 is not 16:9.
    nx_castlevania_resolution_changed(c, original);
    assert(resolution_calls==1);
    expect_render(1280,720);

    selected_index=20; // Index out of bounds.
    nx_castlevania_resolution_changed(c, original);
    assert(resolution_calls==1);

    selected_index=0; // Restore native.
    nx_castlevania_resolution_changed(c, original);
    assert(resolution_calls==2 && width==1920 && height==1080);
    expect_render(1920,1080);

    // Malformed table cannot cause out-of-bounds read.
    put(at(choices)+24, uint32_t(65));
    selected_index=1;
    nx_castlevania_resolution_changed(c, original);
    assert(resolution_calls==2);
    put(at(choices)+24, uint32_t(3));

    // No class method is explicit error instead of calling address zero.
    put(at(klass)+0x198, uint64_t(0));
    denied=false;
    try { nx_castlevania_resolution_changed(c, original); }
    catch (const std::runtime_error& e) {
        denied=std::string(e.what()).find("method")!=std::string::npos;
    }
    assert(denied && resolution_calls==2);
    put(at(klass)+0x198, selector_method);

    // The original still runs if the managed setting was not allocated.
    put(at(receiver)+0x68,uint64_t(0));
    const int before=selection_calls;
    nx_castlevania_resolution_changed(c, original);
    assert(selection_calls==before && resolution_calls==2);
}
