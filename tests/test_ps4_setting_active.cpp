#include <nx/runtime.h>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>
#include <string_view>

void nx_castlevania_setting_active(nx::CPU&, void (*)(nx::CPU&));

namespace {
int called = 0;
void original(nx::CPU& cpu) {
    ++called;
    cpu.x[0] = 0xBEEF;
}
struct ManagedString {
    alignas(8) std::array<unsigned char, 160> bytes{};
    uint64_t pointer() const { return reinterpret_cast<uint64_t>(bytes.data()); }
    void put(std::u16string_view text) {
        const int32_t count = static_cast<int32_t>(text.size());
        std::memcpy(bytes.data() + 16, &count, sizeof(count));
        std::memcpy(bytes.data() + 20, text.data(), text.size() * sizeof(char16_t));
    }
};
}
namespace nx {
[[noreturn]] void fatal(const char* message, ...) {
    throw std::runtime_error(message);
}
}
int main() {
    nx::CPU c{};
    ManagedString name;
    name.put(u"video/windowmode");
    c.x[0] = 0x123; c.x[1] = name.pointer();
    nx_castlevania_setting_active(c, original);
    assert(c.x[0] == 1 && c.x[1] == name.pointer() && called == 0);

    name.put(u"video/resolution");
    c.x[0] = 0x123;
    nx_castlevania_setting_active(c, original);
    assert(c.x[0] == 1 && called == 0);

    name.put(u"audio/master");
    c.x[0] = 0x123;
    nx_castlevania_setting_active(c, original);
    assert(c.x[0] == 0xBEEF && called == 1);

    c.x[1] = 0;
    c.x[0] = 0x123;
    nx_castlevania_setting_active(c, original);
    assert(c.x[0] == 0xBEEF && called == 2);

    // A length mismatch must not activate the video option by prefix.
    name.put(u"video/resolutio");
    c.x[1] = name.pointer();
    nx_castlevania_setting_active(c, original);
    assert(called == 3 && c.x[0] == 0xBEEF);

    // The original is mandatory only for keys we do not handle.
    bool failed_closed = false;
    try { nx_castlevania_setting_active(c, nullptr); }
    catch (const std::runtime_error& e) {
        failed_closed = std::string(e.what()).find("original") != std::string::npos;
    }
    assert(failed_closed);

    name.put(u"video/resolution");
    c.x[0] = 0;
    nx_castlevania_setting_active(c, nullptr);
    assert(c.x[0] == 1 && called == 3);
}
