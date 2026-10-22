#include "platform.h"
#include <cassert>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <string>
#include <sys/stat.h>
#include <unistd.h>

int main() {
    char path[] = "/tmp/kazuma-files-XXXXXX";
    char* root = ::mkdtemp(path);
    assert(root != nullptr);
    const std::string dir = std::string(root) + "/a/b";
    assert(nx::plat::make_dirs(dir));
    assert(nx::plat::make_dirs(dir)); // idempotente
    assert(!nx::plat::make_dirs(dir + "/../escape"));
    const std::string filename = dir + "/arquivo.dat";
    FILE* f = nx::plat::fopen_utf8(filename, "wb");
    assert(f != nullptr);
    assert(std::fwrite("abcdef", 1, 6, f) == 6);
    std::fclose(f);
    f = nx::plat::fopen_utf8(filename, "rb");
    assert(f != nullptr);
    assert(nx::plat::fseek64(f, 2, SEEK_SET) == 0);
    assert(nx::plat::ftell64(f) == 2);
    char buf[4]{};
    assert(nx::plat::read_at(f, 1, buf, 3) == 3);
    assert(std::memcmp(buf, "bcd", 3) == 0);
    assert(nx::plat::ftell64(f) == 2); // pread nao modifica posicao
    assert(nx::plat::read_at(f, 20, buf, 3) == 0); // EOF
    assert(nx::plat::read_at(f, -1, buf, 3) == 0);
    std::fclose(f);
    assert(::unlink(filename.c_str()) == 0);
    assert(::rmdir(dir.c_str()) == 0);
    assert(::rmdir((std::string(root) + "/a").c_str()) == 0);
    assert(::rmdir(root) == 0);
    std::puts("OK: 5 funcoes de arquivo testadas em Linux; PS4 AINDA NAO TESTADO.");
}
