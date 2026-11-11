// Lingshu 144 - PS4 userland platform adapter: POSIX core only.
// No GPU, no audio, no memory mapper. This file is not a game executable.
#include "platform.h"
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <time.h>
#include <sched.h>
#include <unistd.h>
#include <sys/types.h>
#include <climits>
#include <mutex>
#include <sys/stat.h>
#include <cstring>

namespace nx::plat {

FILE* fopen_utf8(const std::string& path, const char* mode) {
    return std::fopen(path.c_str(), mode);
}
int64_t ftell64(FILE* file) { return static_cast<int64_t>(ftello(file)); }
int fseek64(FILE* file, int64_t offset, int whence) {
    return fseeko(file, static_cast<off_t>(offset), whence);
}
uint64_t read_at(FILE* file, int64_t offset, void* dest, uint64_t len) {
    if (!file || !dest || offset < 0 || len > uint64_t(SSIZE_MAX)) return 0;
    const int fd = fileno(file);
    if (fd < 0) return 0;
    uint64_t done = 0;
    while (done < len) {
        ssize_t n = pread(fd, static_cast<unsigned char*>(dest) + done,
                          static_cast<size_t>(len-done),
                          static_cast<off_t>(offset + static_cast<int64_t>(done)));
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) break;
        done += static_cast<uint64_t>(n);
    }
    return done;
}
// The PS4 homebrew stderr may not be visible in the user's UI. Persist
// boot and runtime diagnostics for FTP retrieval, with bounded file growth.
// The default /data path remains unverified on PS4 hardware.
std::string data_root() {
    const char* value=std::getenv("KAZUMA_DATA_ROOT");
    if (value && value[0]=='/' && std::strlen(value)<256) return value;
    return "/data/kazuma-lab";
}
void log_line(const char* line) {
    static std::mutex lock;
    static bool initialized=false;
    static FILE* file=nullptr;
    static std::string path;
    std::lock_guard<std::mutex> guard(lock);
    const char* msg=line ? line : "";
    std::fprintf(stderr,"%s\n",msg);
    if (!initialized) {
        initialized=true;
        const std::string root=data_root();
        if (mkdir(root.c_str(),0700)==0 || errno==EEXIST) {
            path=root+"/boot.log";
            file=std::fopen(path.c_str(),"ab");
        }
    }
    if (!file) return;
    const long offset=std::ftell(file);
    if (offset>=2*1024*1024) {
        std::fclose(file);
        file=std::fopen(path.c_str(),"wb");
        if (!file) return;
    }
    if (std::fprintf(file,"%s\n",msg)<0 || std::fflush(file)!=0) {
        std::fclose(file);
        file=nullptr;
    }
}
std::string setting(const std::string&) { return {}; } // No config backend yet.
uint64_t monotonic_ns() {
    timespec now{};
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return 0;
    return uint64_t(now.tv_sec)*1000000000ull+uint64_t(now.tv_nsec);
}
void sleep_ns(int64_t ns) {
    if (ns <= 0) return;
    timespec req{time_t(ns/1000000000), long(ns%1000000000)};
    while (nanosleep(&req,&req) != 0 && errno == EINTR) {}
}
void yield() { sched_yield(); }
} // namespace nx::plat
