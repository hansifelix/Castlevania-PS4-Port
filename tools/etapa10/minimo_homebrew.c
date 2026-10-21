/* Kazuma Port Games BR — Etapa 10.
   Teste independente de ligacao OpenOrbis: NENHUMA rotina do Castlevania.
   Sem desenho de tela, entrada de controle, PKG, eboot ou execucao no PS4. */
static volatile unsigned int marca = 0;

int main(void) {
    marca = 20261021u;
    return marca == 20261021u ? 0 : 1;
}
