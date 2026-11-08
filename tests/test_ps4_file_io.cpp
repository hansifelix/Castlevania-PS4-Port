// Host POSIX test of the same PS4 file-provider source (no game data).
#include <platform.h>
#include <cassert>
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <string>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>

int main() {
    char tmp[] = "/tmp/kazuma-file-io-XXXXXX";
    char* root = mkdtemp(tmp);
    assert(root);
    const std::string r(root);
    const std::string folder = r + "/a/b/c";
    assert(nx::plat::make_dirs(folder));
    assert(nx::plat::make_dirs(folder)); // idempotent
    assert(!nx::plat::make_dirs(""));
    assert(!nx::plat::make_dirs(r + "/a/../escape"));
    const std::string file = folder + "/real.bin";
    FILE* f = nx::plat::fopen_utf8(file, "w+b");
    assert(f);
    const char content[] = "Castlevania-PS4-runtime-file-test";
    assert(fwrite(content, 1, sizeof(content), f) == sizeof(content));
    assert(fflush(f) == 0);
    assert(nx::plat::fseek64(f, 5, SEEK_SET) == 0);
    const auto before = nx::plat::ftell64(f);
    assert(before == 5);
    char bytes[16]{};
    assert(nx::plat::read_at(f, 0, bytes, 11) == 11);
    assert(std::memcmp(bytes, content, 11) == 0);
    assert(nx::plat::ftell64(f) == before);
    assert(nx::plat::read_at(f, 100000, bytes, 11) == 0); // genuine EOF
    assert(nx::plat::ftell64(f) == before);
    assert(nx::plat::read_at(f, -1, bytes, 4) == 0);
    assert(nx::plat::read_at(f, 0, nullptr, 4) == 0);
    assert(nx::plat::read_at(nullptr, 0, bytes, 4) == 0);
    assert(nx::plat::fseek64(f, 0, SEEK_END) == 0);
    assert(nx::plat::ftell64(f) == sizeof(content));
    assert(nx::plat::fseek64(nullptr, 0, SEEK_SET) == -1);
    assert(nx::plat::ftell64(nullptr) == -1);
    assert(fclose(f) == 0);
    assert(nx::plat::fopen_utf8(file, nullptr) == nullptr);
    assert(nx::plat::fopen_utf8("", "rb") == nullptr);
    assert(unlink(file.c_str()) == 0);
    assert(rmdir(folder.c_str()) == 0);
    assert(rmdir((r + "/a/b").c_str()) == 0);
    assert(rmdir((r + "/a").c_str()) == 0);
    assert(rmdir(r.c_str()) == 0);
}
