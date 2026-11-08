#include <nx/runtime.h>
#include "castlevania_resolution.hpp"
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>
#include <string_view>

void nx_castlevania_video_text(nx::CPU&, void (*)(nx::CPU&));

namespace {
using Memory = std::array<uint8_t, 320>;
alignas(8) Memory allocated{};
int original_calls = 0;
int allocator_calls = 0;
uint64_t original_arg = 0;
void original(nx::CPU& c) { ++original_calls; original_arg = c.x[1]; }
uint64_t ptr(Memory& m) { return reinterpret_cast<uint64_t>(m.data()); }
template<class T> void put(uint64_t at, T v) {
    std::memcpy(reinterpret_cast<void*>(at), &v, sizeof(v));
}
template<class T> T get(uint64_t at) {
    T out{}; std::memcpy(&out, reinterpret_cast<const void*>(at), sizeof(out)); return out;
}
void set_string(Memory& m, std::u16string_view value) {
    m.fill(0);
    put<int32_t>(ptr(m)+16, static_cast<int32_t>(value.size()));
    std::memcpy(m.data()+20, value.data(), value.size()*sizeof(char16_t));
}
void assert_label(uint64_t addr, std::u16string_view wanted) {
    assert(get<int32_t>(addr+16) == static_cast<int32_t>(wanted.size()));
    for(size_t i=0;i<wanted.size();++i)
        assert(get<char16_t>(addr+20+i*2) == wanted[i]);
}
}
namespace nx {
void call(CPU& c, uint64_t address) {
    assert(address == NX_BASE + 0x418f160ull);
    ++allocator_calls;
    assert(c.x[1] == 0);
    assert(c.x[0] < 80);
    allocated.fill(0);
    put<int32_t>(ptr(allocated) + 16, static_cast<int32_t>(c.x[0]));
    c.x[0] = ptr(allocated);
}
[[noreturn]] void fatal(const char* msg, ...) { throw std::runtime_error(msg); }
[[noreturn]] void unimpl(CPU&, uint64_t, const char* msg) { throw std::runtime_error(msg); }
void log(const char*, ...) {}
}
int main() {
    using namespace kazuma::ps4::video;
    nx::CPU c{};
    alignas(8) Memory self{}, source{}, existing{};
    set_string(source, u"3840x2160");
    set_string(existing, u"unchanged");
    put<uint64_t>(ptr(self)+0xd8, ptr(existing));
    c.x[0] = ptr(self);
    c.x[1] = ptr(source);
    bool missing = false;
    try { nx_castlevania_video_text(c, nullptr); }
    catch (const std::runtime_error& e) {
        missing = std::string(e.what()).find("original") != std::string::npos;
    }
    assert(missing && original_calls == 0);
    bool unready = false;
    try { nx_castlevania_video_text(c, original); }
    catch (const std::runtime_error& e) {
        unready = std::string(e.what()).find("VideoOut") != std::string::npos;
    }
    assert(unready && original_calls == 0 && allocator_calls == 0);

    assert(configure_native(1920, 1080));
    nx_castlevania_video_text(c, original);
    assert(original_calls == 1 && allocator_calls == 1);
    assert(original_arg == ptr(allocated) && c.x[1] == ptr(allocated));
    assert_label(ptr(allocated), u"1920 \u00d7 1080");

    // Already displayed managed label is reused without a second allocation.
    put<uint64_t>(ptr(self)+0xd8, ptr(allocated));
    c.x[1] = ptr(source);
    nx_castlevania_video_text(c, original);
    assert(original_calls == 2 && allocator_calls == 1);
    assert(c.x[1] == ptr(allocated));

    // A changed number is not a legitimate 3840x2160 native label.
    set_string(source, u"3840x2161");
    c.x[1] = ptr(source);
    nx_castlevania_video_text(c, original);
    assert(original_calls == 3 && allocator_calls == 1);
    assert(original_arg == ptr(source));

    // UTF-16 multiplication sign and spaces are accepted by the actual hook.
    set_string(source, u"3840 \u00d7 2160");
    c.x[1] = ptr(source);
    nx_castlevania_video_text(c, original);
    assert(original_calls == 4 && allocator_calls == 1);
    assert(original_arg == ptr(allocated));

    // On a native 4K display the game's original label is preserved.
    assert(configure_native(3840, 2160));
    c.x[1] = ptr(source);
    nx_castlevania_video_text(c, original);
    assert(original_calls == 5 && allocator_calls == 1);
    assert(original_arg == ptr(source));
}
