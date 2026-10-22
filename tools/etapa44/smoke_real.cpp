// Etapa 44 — exercicio de ligacao do codigo publico, sem arquivos comerciais.
// NAO e o jogo nem autoriza usar este ELF diretamente no PS4.
#include "platform.h"
#include <cstdint>
#include <cstdio>
#include <string>

// Funcao separada impede confundir teste de link com execucao de E/S.
static int verificar_arquivos() {
    // Apenas caminhos de leitura; nunca grava em arquivos do usuario.
    const std::string arquivo = "/app0/sce_sys/param.sfo";
    FILE* fp = nx::plat::fopen_utf8(arquivo, "rb");
    if (!fp) return 2;
    const int64_t pos = nx::plat::ftell64(fp);
    const int rc = nx::plat::fseek64(fp, 0, SEEK_SET);
    unsigned char cabecalho[8]{};
    const uint64_t lidos = nx::plat::read_at(fp, 0, cabecalho, sizeof cabecalho);
    std::fclose(fp);
    return (pos >= 0 && rc == 0 && lidos > 0) ? 0 : 3;
}

int main() {
    nx::plat::log_line("KAZUMA 44: teste de adaptadores; nao e Castlevania");
    const uint64_t inicio = nx::plat::monotonic_ns();
    nx::plat::sleep_ns(1000000);
    const uint64_t fim = nx::plat::monotonic_ns();
    // make_dirs esta presente no objeto e no link, mas NAO e executada:
    // um ELF de diagnostico nao deve criar diretorios no PS4.
    const int arquivos = verificar_arquivos();
    return (fim >= inicio && arquivos != 3) ? 0 : 1;
}
