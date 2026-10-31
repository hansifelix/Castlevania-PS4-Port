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

constexpr const char* kExpectedModules[3] = {"main", "sdk", "subsdk0"};

bool correct_module(const char* name, size_t position) {
    return name && position < 3 && std::strcmp(name, kExpectedModules[position]) == 0;
}

bool patch_address_valid(const nx::ModuleInfo& module, uint64_t offset,
                         uint64_t image_length) {
    // Mirror nx::load_modules' AOT patch contract without overflowing any end address.
    if ((offset & 3) || module.text > UINT64_MAX - module.text_size) return false;
    const uint64_t text_end = module.text + module.text_size;
    return offset >= module.text && offset <= text_end &&
           offset <= image_length && text_end >= 4 &&
           offset <= text_end - 4 && offset <= image_length - 4;
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

    for (size_t position = 0; position < modules.size(); ++position) {
        const nx::ModuleInfo* module = modules[position];
        if (!module || !correct_module(module->name, position))
            return report_failure("LINGSHU174: module order/name mismatch with pinned AOT");
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
        if (measured < 0 || static_cast<uint64_t>(measured) != required) {
            std::fclose(f);
            char log[350];
            std::snprintf(log, sizeof(log),
                          "LINGSHU172: wrong flat image length for %s (expected %llu, got %lld)",
                          module->name,
                          static_cast<unsigned long long>(required),
                          static_cast<long long>(measured));
            return report_failure(log);
        }

        // The AOT generator pins ARM64 opcodes for this exact game update.
        // nx::load_modules checks the same patches after allocating guest memory.
        // Validate early, without allocating that memory or starting the engine.
        if (module->instruction_patch_count && !module->instruction_patches) {
            std::fclose(f);
            return report_failure("LINGSHU174: AOT patch metadata missing");
        }
        for (size_t i = 0; i < module->instruction_patch_count; ++i) {
            const auto& patch = module->instruction_patches[i];
            if (!patch_address_valid(*module, patch.offset, required) ||
                patch.offset > static_cast<uint64_t>(std::numeric_limits<int64_t>::max()) ||
                nx::plat::fseek64(f, static_cast<int64_t>(patch.offset), SEEK_SET) != 0) {
                std::fclose(f);
                return report_failure("LINGSHU174: malformed AOT instruction patch bounds");
            }
            unsigned char raw[4]{};
            const bool read_ok = std::fread(raw, 1, sizeof raw, f) == sizeof raw;
            const uint32_t opcode = uint32_t(raw[0]) | (uint32_t(raw[1]) << 8) |
                                    (uint32_t(raw[2]) << 16) | (uint32_t(raw[3]) << 24);
            if (!read_ok || opcode != patch.expected) {
                std::fclose(f);
                return report_failure("LINGSHU174: image opcode mismatch: wrong game update/AOT pair");
            }
        }
        std::fclose(f);

    }

    nx::plat::log_line("LINGSHU172: all three AOT module lengths and version patch opcodes verified; starting real nx::boot");
    // This means only that required images are present at the expected lengths.
    // It does NOT guarantee valid contents, ROMFS, GPU backend or game boot.
    return true;
}
