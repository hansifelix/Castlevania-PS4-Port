// Etapa 80 — assinatura textual do trabalho próprio do projeto.
// Usada no diagnóstico nativo e disponível para os créditos in-game
// quando existir uma interface gráfica funcional. NÃO é um logo do jogo.
// O conteúdo e os direitos do jogo original pertencem a seus titulares.
#include "kazuma_branding.hpp"

namespace {
constexpr char kBrand[] = "Kazuma Traduções";
constexpr char kCredit[] = "Port PS4 experimental por Kazuma Traduções";
constexpr char kNotice[] = "Castlevania: Belmont's Curse - jogo original de seus respectivos titulares.";
} // namespace

extern "C" const char* kazuma_port_brand(void) { return kBrand; }
extern "C" const char* kazuma_port_credit(void) { return kCredit; }
extern "C" const char* kazuma_original_game_notice(void) { return kNotice; }
