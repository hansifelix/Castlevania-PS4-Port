// Homebrew minimo para verificar a cadeia OpenOrbis no PS4.
// Nao contem codigo de Castlevania, arquivos Switch ou grafico.
#include <stdio.h>
#include <orbis/libkernel.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("Castlevania PS4 Port - teste independente do SDK (sem jogo)\n");
    // Manter o processo vivo evita que ele saia imediatamente.
    while (true) {
        sceKernelUsleep(1000000);
    }
    return 0;
}
