// Kazuma Port Games BR, Etapa 40: parte real da interface nx::plat.
// Compilacao + testes offline. NAO significa funcionamento no PS4.
// O aplicativo deve validar um caminho de dados gravavel antes de utilizar estas funcoes.
#include "platform.h"
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <string>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

namespace nx::plat {

FILE* fopen_utf8(const std::string& path, const char* mode) {
    if (path.empty() || !mode || !*mode) return nullptr;
    return std::fopen(path.c_str(), mode);
}

int64_t ftell64(FILE* f) {
    if (!f) return -1;
    const off_t pos = ::ftello(f);
    return pos < 0 ? -1 : static_cast<int64_t>(pos);
}

int fseek64(FILE* f, int64_t off, int origin) {
    if (!f) return -1;
    if (off < static_cast<int64_t>(std::numeric_limits<off_t>::min()) ||
        off > static_cast<int64_t>(std::numeric_limits<off_t>::max())) return -1;
    return ::fseeko(f, static_cast<off_t>(off), origin);
}

// Ler numa posicao sem modificar o offset compartilhado do FILE*. Alinhado ao contrato upstream.
uint64_t read_at(FILE* f, int64_t off, void* buf, uint64_t size) {
    if (!f || !buf || off < 0 || size == 0) return 0;
    if (size > static_cast<uint64_t>(std::numeric_limits<ssize_t>::max())) return 0;
    const int fd = ::fileno(f);
    if (fd < 0) return 0;
    uint64_t done = 0;
    while (done < size) {
        if (done > static_cast<uint64_t>(std::numeric_limits<int64_t>::max() - off)) break;
        const auto amount = static_cast<size_t>(size - done);
        const auto offset = static_cast<off_t>(off + static_cast<int64_t>(done));
        const ssize_t got = ::pread(fd, static_cast<unsigned char*>(buf) + done, amount, offset);
        if (got < 0 && errno == EINTR) continue;
        if (got <= 0) break;
        done += static_cast<uint64_t>(got);
    }
    return done;
}

// Cria os diretorios solicitados. Rejeita '..' para nao escapar do diretorio base.
// Na plataforma real, uma raiz gravavel autorizada ainda devera ser configurada.
bool make_dirs(const std::string& path) {
    if (path.empty()) return false;
    std::string current = (path.front() == '/') ? "/" : "";
    size_t at = (path.front() == '/') ? 1 : 0;
    bool has_segment = false;
    while (at < path.size()) {
        const size_t slash = path.find('/', at);
        const std::string part = path.substr(at, slash == std::string::npos ? slash : slash - at);
        at = slash == std::string::npos ? path.size() : slash + 1;
        if (part.empty() || part == ".") continue;
        if (part == "..") return false;
        if (!current.empty() && current.back() != '/') current.push_back('/');
        current += part;
        has_segment = true;
        if (::mkdir(current.c_str(), 0755) != 0 && errno != EEXIST) return false;
        struct stat st {};
        if (::stat(current.c_str(), &st) != 0 || !S_ISDIR(st.st_mode)) return false;
    }
    return has_segment;
}

} // namespace nx::plat
