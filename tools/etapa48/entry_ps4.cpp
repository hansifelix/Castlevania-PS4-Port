// Etapa 48: ponto de entrada REAL para estudar nx::boot do runtime publico.
// Nao fornece modulos de jogo nem substitui símbolos ausentes por stubs.
namespace nx { void boot(); }
int main() {
    nx::boot();
    return 0;
}
