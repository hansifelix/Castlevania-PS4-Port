#include <nx/runtime.h>
#include "castlevania_resolution.hpp"
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>

void nx_castlevania_video_defaults(nx::CPU&, void (*)(nx::CPU&));

namespace nx {
uint64_t test_static_usage_pointer = 0;
[[noreturn]] void fatal(const char* text, ...) { throw std::runtime_error(text); }
[[noreturn]] void unimpl(CPU&, uint64_t, const char* text) { throw std::runtime_error(text); }
void log(const char*, ...) {}
}
namespace {
using Bytes = std::array<uint8_t, 192>;
int original_calls = 0;
void original(nx::CPU&) { ++original_calls; }
uint64_t ptr(const Bytes& b) { return reinterpret_cast<uint64_t>(b.data()); }
template <typename T> void put(uint64_t addr, T value) {
    std::memcpy(reinterpret_cast<void*>(addr), &value, sizeof(T));
}
template <typename T> T read(uint64_t addr) {
    T result{}; std::memcpy(&result, reinterpret_cast<const void*>(addr), sizeof(T)); return result;
}
void populate(Bytes& usage, Bytes& klass, Bytes& fields, Bytes& a, Bytes& b) {
    nx::test_static_usage_pointer = ptr(usage);
    put(ptr(usage), ptr(klass));
    put(ptr(klass) + 0xb8, ptr(fields));
    put(ptr(fields), ptr(a));
    put(ptr(fields) + 8, ptr(b));
    put<uint32_t>(ptr(a) + 24, 12);
    put<uint32_t>(ptr(b) + 24, 12);
    put<uint32_t>(ptr(a) + 32 + 11*8, 3840);
    put<uint32_t>(ptr(a) + 32 + 11*8 + 4, 2160);
    put<uint32_t>(ptr(b) + 32 + 11*8, 3840);
    put<uint32_t>(ptr(b) + 32 + 11*8 + 4, 2160);
}
}
int main() {
    using namespace kazuma::ps4::video;
    nx::CPU cpu{};
    alignas(8) Bytes usage{}, klass{}, fields{}, a{}, b{};
    populate(usage, klass, fields, a, b);
    bool failed = false;
    try { nx_castlevania_video_defaults(cpu, nullptr); }
    catch (const std::runtime_error& e) {
        failed = std::string(e.what()).find("original") != std::string::npos;
    }
    assert(failed && original_calls == 0);

    failed = false;
    try { nx_castlevania_video_defaults(cpu, original); }
    catch (const std::runtime_error& e) {
        failed = std::string(e.what()).find("VideoOut") != std::string::npos;
    }
    assert(failed && original_calls == 1);
    assert(read<uint32_t>(ptr(a) + 32 + 11*8) == 3840);
    assert(configure_native(1920, 1080));
    nx_castlevania_video_defaults(cpu, original);
    assert(original_calls == 2);
    for (const auto& list : {ptr(a), ptr(b)}) {
        assert(read<uint32_t>(list + 32 + 11*8) == 1920);
        assert(read<uint32_t>(list + 32 + 11*8 + 4) == 1080);
        assert(read<uint32_t>(list + 32 + 10*8) == 0);
    }
    // A changed list shape must not be modified.
    put<uint32_t>(ptr(b) + 24, 11);
    put<uint32_t>(ptr(b) + 32 + 11*8, 777);
    assert(configure_native(1280, 720));
    nx_castlevania_video_defaults(cpu, original);
    assert(original_calls == 3);
    assert(read<uint32_t>(ptr(a) + 32 + 11*8) == 1280);
    assert(read<uint32_t>(ptr(b) + 32 + 11*8) == 777);

    // Missing type metadata is not permission to write an arbitrary array.
    nx::test_static_usage_pointer = 0;
    nx_castlevania_video_defaults(cpu, original);
    assert(original_calls == 4);
    assert(read<uint32_t>(ptr(a) + 32 + 11*8) == 1280);
}
