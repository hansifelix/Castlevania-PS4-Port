// Kazuma - Etapa 49 - primeiros servicos de host nao graficos.
// Adaptacoes limitadas ao contrato publico nx::plat (MIT, upstream fixado).
// Nenhuma funcao grafica/sonora/memoria e falsificada.
// O data_root() /app0 e apenas provisoriamente LEITURA para recursos
// empacotados; NAO habilita saves, runtime do jogo nem escrita em /app0.
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <string>

namespace nx::plat {

// Sem modo headless no homebrew PS4 atual: contrato da interface do host.
bool headless() { return false; }

// Como documentado na interface publica: zero onde guarda de memoria nao existe.
uint64_t memguard_overlap_ns(uint64_t, uint64_t) { return 0; }

// Profiling amostral do PC host nao implementado: a API admite "false".
bool profile(const int64_t*, const uint64_t* const*, size_t,
             int, const std::string&) { return false; }

// Parametros NX_* opcionais. Permite configuracao no processo se o host
// suportar getenv; nao depende de filesystem gravavel.
std::string setting(const std::string& key) {
    std::string env("NX_");
    for (char c : key) {
        if (c >= 'a' && c <= 'z') c = static_cast<char>(c - 'a' + 'A');
        const bool allowed = (c >= 'A' && c <= 'Z') ||
                             (c >= '0' && c <= '9') || c == '_';
        if (!allowed) return {};
        env.push_back(c);
    }
    if (const char* v = std::getenv(env.c_str())) return std::string(v);
    return {};
}

// Caminho de recursos EMBUTIDOS no PKG; antes de usar nx::boot() com jogo,
// separar uma area privada gravavel para analises/saves/configuracoes.
std::string data_root() {
    if (const char* v = std::getenv("NX_DATA_ROOT")) {
        if (v[0] == '/') return std::string(v);
    }
    return "/app0";
}

[[noreturn]] void exit_process(int code) { std::exit(code); }

}  // namespace nx::plat
