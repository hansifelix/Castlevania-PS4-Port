// Kazuma Traducoes: fail-closed package asset root and read-only settings.
// On PS4, /app0 is the package mount. The ROM assets and AOT analysis MUST
// actually exist there; returning a made-up "success" would hide a missing game.
// No user savedata mount is claimed. No proprietary assets live in this file.
#include <platform.h>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <sys/stat.h>

#if defined(KAZUMA_PS4)
#include <orbis/libkernel.h>
#elif !defined(__linux__)
#error "Explicit KAZUMA_PS4 or Linux host-only test target required"
#endif

namespace nx::plat {
namespace {
bool directory(const std::string& path) {
    struct stat st {};
    return ::stat(path.c_str(), &st) == 0 && S_ISDIR(st.st_mode);
}
bool regular_file(const std::string& path) {
    struct stat st {};
    return ::stat(path.c_str(), &st) == 0 && S_ISREG(st.st_mode) &&
           st.st_size >= 0 && st.st_size <= 16384;
}
bool valid_root(const std::string& path) {
    // Require fully staged, real assets. A plain /app0/eboot.bin is not enough.
    return !path.empty() && path.front() == '/' &&
           path.find("/../") == std::string::npos &&
           path.find("/./") == std::string::npos &&
           path.find("//") == std::string::npos &&
           path.back() != '/' &&
           directory(path) &&
           directory(path + "/analysis") &&
           directory(path + "/extract/romfs");
}
std::string candidate_root() {
#if defined(KAZUMA_PS4)
    return "/app0";
#else
    // Host regression only. Never used in actual PS4 builds.
    const char* root = std::getenv("KAZUMA_TEST_APP0_ROOT");
    return root ? std::string(root) : std::string();
#endif
}
void write_log(const char* line) {
    if (!line) return;
#if defined(KAZUMA_PS4)
    // Format string is constant; a game log line cannot inject % specifiers.
    sceKernelDebugOutText(0, "%s\n", line);
#else
    std::fprintf(stderr, "%s\n", line);
#endif
}
[[noreturn]] void missing_assets() {
    write_log("Kazuma PS4: missing analysis/ or extract/romfs/ in app0; refusing to boot");
    std::abort();
}
std::string trim(std::string value) {
    const size_t first = value.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) return {};
    const size_t last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}
bool safe_key(const std::string& key) {
    if (key.empty() || key.size() > 64) return false;
    for (unsigned char c : key)
        if (!std::isalnum(c) && c != '_' && c != '-') return false;
    return true;
}
} // namespace

void log_line(const char* line) { write_log(line); }

std::string data_root() {
    const std::string root = candidate_root();
    if (!valid_root(root)) missing_assets();
    return root;
}

std::string setting(const std::string& key) {
    if (!safe_key(key)) return {};
    // An optional, read-only file packaged alongside the executable.
    // Never write back to /app0: that mount is read-only on a real PS4.
    const std::string path = data_root() + "/kazuma-settings.cfg";
    if (!regular_file(path)) return {};
    FILE* file = std::fopen(path.c_str(), "rb");
    if (!file) return {};
    char line[512];
    std::string answer;
    while (std::fgets(line, sizeof(line), file)) {
        // Reject overlong lines rather than interpreting a truncated value.
        if (!std::strchr(line, '\n') && !std::feof(file)) {
            int ch = 0;
            while ((ch = std::fgetc(file)) != EOF && ch != '\n') {}
            continue;
        }
        const std::string content = trim(line);
        if (content.empty() || content[0] == '#' || content[0] == ';') continue;
        const size_t equals = content.find('=');
        if (equals == std::string::npos) continue;
        if (trim(content.substr(0, equals)) == key) {
            answer = trim(content.substr(equals + 1));
            break;
        }
    }
    std::fclose(file);
    return answer;
}
} // namespace nx::plat
