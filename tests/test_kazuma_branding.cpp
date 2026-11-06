#include "runtime_bridge/kazuma_branding.hpp"
#include <cassert>
#include <cstring>

int main() {
    auto brand = kazuma_port_brand();
    auto credit = kazuma_port_credit();
    auto original = kazuma_original_game_notice();
    assert(brand && std::strstr(brand, "Kazuma Traducoes"));
    assert(credit && std::strstr(credit, "Port PS4 experimental"));
    assert(original && std::strstr(original, "respectivos titulares"));
    assert(std::strstr(original, "Kazuma") == nullptr);
    return 0;
}
