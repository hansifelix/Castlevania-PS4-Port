// Lingshu 172 — native boot gate using the REAL AOT ModuleInfo table.
// No synthetic frame, text/blue screen or fake engine success.
// nx::boot() calls load_modules() which requires analysis/<module>.bin and
// checks that each decompressed image is exactly data + data_size bytes.
// The original NSO files (ExeFS/main, sdk, subsdk0) are NOT those flat images.
// Produce them from your own NSOs with upstream tools/nso2bin.py off-console.
#include <nx/module.h>
#include "platform.h"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <string>

namespace {
bool report_failure(const char* message) {
    nx::plat::log_line(message);
    return false;
}

bool known_module(const char* name) {
    return name &&
           (!std::strcmp(name, "main") ||
            !std::strcmp(name, "sdk") ||
            !std::strcmp(name, "subsdk0"));
}
} // namespace

extern "C" bool lingshu_ps4_boot_images_present() {
    const auto modules = nx::linked_modules();
    if (modules.size() != 3 || !modules[0] ||
        !modules[0]->name || std::strcmp(modules[0]->name, "main") != 0)
        return report_failure("LINGSHU172: invalid AOT module table (expected main first, 3 modules)");

    const std::string root = nx::plat::data_root();
    if (root.empty())
        return report_failure("LINGSHU172: data_root empty; module images not accessible");

    for (const nx::ModuleInfo* module : modules) {
        if (!module || !known_module(module->name))
            return report_failure("LINGSHU172: missing/unknown AOT module");
        if (module->data > std::numeric_limits<uint64_t>::max() - module->data_size)
            return report_failure("LINGSHU172: invalid module image size overflow");

        const uint64_t required = module->data + module->data_size;
        if (!required || required > uint64_t(std::numeric_limits<int64_t>::max()))
            return report_failure("LINGSHU172: invalid module image length");

        const std::string path = root + "/analysis/" + module->name + ".bin";
        FILE* f = nx::plat::fopen_utf8(path, "rb");
        if (!f) {
            char log[300];
            std::snprintf(log, sizeof(log), "LINGSHU172: missing required flat image: %s", path.c_str());
            return report_failure(log);
        }
        int64_t measured = -1;
        if (nx::plat::fseek64(f, 0, SEEK_END) == 0)
            measured = nx::plat::ftell64(f);
        std::fclose(f);

        if (measured < 0 || static_cast<uint64_t>(measured) != required) {
            char log[350];
            std::snprintf(log, sizeof(log),
                          "LINGSHU172: wrong flat image length for %s (expected %llu, got %lld)",
                          module->name,
                          static_cast<unsigned long long>(required),
                          static_cast<long long>(measured));
            return report_failure(log);
        }
    }

    nx::plat::log_line("LINGSHU172: all three AOT module image lengths verified; starting real nx::boot");
    // This means only that required images are present at the expected lengths.
    // It does NOT guarantee valid contents, ROMFS, GPU backend or game boot.
    return true;
}
