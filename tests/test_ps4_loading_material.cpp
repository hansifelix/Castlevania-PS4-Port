#include <nx/runtime.h>
#include <cassert>
#include <array>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>

void nx_castlevania_loading_material(nx::CPU& c, void (*original)(nx::CPU&));
namespace {
unsigned originals = 0, guest_calls = 0, logs = 0;
uint64_t original_x0 = 0, material_x0 = 0, prepare_index = 0;
float prepare_frame = -1;
void original(nx::CPU& cpu) { ++originals; original_x0 = cpu.x[0]; }
template <typename T> void put(uint64_t ptr, T value) {
    std::memcpy(reinterpret_cast<void*>(ptr), &value, sizeof(T));
}
}
namespace nx {
void call(CPU& c, uint64_t addr) {
    ++guest_calls;
    if (addr == NX_BASE + 0x1dcc470) {
        assert(c.x[1] == 0);
        c.v[0].f32[0] = 2.5f;
    } else if (addr == NX_BASE + 0x4e1aba0) {
        material_x0 = c.x[0];
        prepare_index = c.x[1];
        assert(c.x[2] == 0);
        prepare_frame = c.v[0].f32[0];
    } else {
        throw std::logic_error("unexpected guest target");
    }
}
[[noreturn]] void fatal(const char* message, ...) { throw std::runtime_error(message); }
void log(const char*, ...) { ++logs; }
}
int main() {
    nx::CPU c{};
    // Missing object -> call original, never allocate/rewrite materials.
    nx_castlevania_loading_material(c, original);
    assert(originals == 1 && guest_calls == 0 && logs == 0);
    assert(!original_x0);
    bool missing_original = false;
    try { nx_castlevania_loading_material(c, nullptr); }
    catch (const std::runtime_error& ex) {
        missing_original = std::string(ex.what()).find("original") != std::string::npos;
    }
    assert(missing_original);

    std::array<uint8_t, 160> self{};
    std::array<uint8_t, 96> settings{};
    uint64_t me = reinterpret_cast<uint64_t>(self.data());
    uint64_t st = reinterpret_cast<uint64_t>(settings.data());
    uint64_t material = 0x12345000;
    c.x[0] = me;
    put(me + 0x38, st);
    put(st + 0x18, material);
    put(me + 0x48, uint32_t(17));
    const uint64_t original_expected = c.x[0];
    nx_castlevania_loading_material(c, original);
    assert(originals == 2 && original_x0 == original_expected);
    assert(guest_calls == 2 && logs == 1);
    assert(material_x0 == material && prepare_index == 17);
    assert(prepare_frame == 2.5f);
    // Existing unchanged semantics: no material => skip both AOT calls.
    put(st + 0x18, uint64_t(0));
    nx_castlevania_loading_material(c, original);
    assert(originals == 3 && guest_calls == 2 && logs == 1);
}
