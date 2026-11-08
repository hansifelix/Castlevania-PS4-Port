// Kazuma Traducoes: real POSIX file access providers for nx::plat on PS4.
// This does not mount savedata or choose a data_root: those PS4 services still
// need a separate integration. Never fake a successful file operation.
// File paths/modes are supplied by the upstream game's established FS bridge.
#include <platform.h>
#include <cerrno>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

namespace nx::plat {
namespace {
bool directory_exists(const std::string& path) {
    struct stat st {};
    return stat(path.c_str(), &st) == 0 && S_ISDIR(st.st_mode);
}
bool ensure_directory(const std::string& path) {
    if (path.empty()) return false;
    if (mkdir(path.c_str(), 0755) == 0) return true;
    return errno == EEXIST && directory_exists(path);
}
} // namespace

FILE* fopen_utf8(const std::string& path, const char* mode) {
    if (path.empty() || !mode || !*mode) return nullptr;
    return std::fopen(path.c_str(), mode);
}

int64_t ftell64(FILE* stream) {
    if (!stream) return -1;
    static_assert(sizeof(off_t) >= sizeof(int64_t), "PS4 requires 64-bit off_t");
    const off_t position = ftello(stream);
    return position < 0 ? -1 : static_cast<int64_t>(position);
}

int fseek64(FILE* stream, int64_t offset, int origin) {
    if (!stream) return -1;
    static_assert(sizeof(off_t) >= sizeof(int64_t), "PS4 requires 64-bit off_t");
    return fseeko(stream, static_cast<off_t>(offset), origin);
}

uint64_t read_at(FILE* stream, int64_t offset, void* buffer, uint64_t length) {
    if (!stream || offset < 0 || (!buffer && length != 0)) return 0;
    if (!length) return 0;
    const int fd = fileno(stream);
    if (fd < 0) return 0;
    constexpr size_t kChunk = 1u << 20;
    uint64_t done = 0;
    while (done < length) {
        if (static_cast<uint64_t>(offset) >
            static_cast<uint64_t>(std::numeric_limits<int64_t>::max()) - done)
            break;
        const size_t n = static_cast<size_t>(
            (length - done) < kChunk ? (length - done) : kChunk);
        const ssize_t got = pread(fd, static_cast<unsigned char*>(buffer) + done,
                                  n, static_cast<off_t>(offset + done));
        if (got < 0 && errno == EINTR) continue;
        if (got <= 0) break; // EOF or genuine OS error; never fabricate content.
        done += static_cast<uint64_t>(got);
    }
    // pread never changes the FILE* seek position.
    return done;
}

bool make_dirs(const std::string& path) {
    if (path.empty()) return false;
    std::string component;
    component.reserve(path.size());
    size_t i = 0;
    if (path[0] == '/') { component = "/"; i = 1; }
    while (i < path.size()) {
        const size_t slash = path.find('/', i);
        const std::string token = path.substr(
            i, slash == std::string::npos ? std::string::npos : slash - i);
        if (token == "..") return false; // Reject traversal; do not escape root.
        if (!token.empty() && token != ".") {
            if (!component.empty() && component.back() != '/') component += '/';
            component += token;
            if (!ensure_directory(component)) return false;
        }
        if (slash == std::string::npos) break;
        i = slash + 1;
    }
    return directory_exists(component);
}
} // namespace nx::plat
