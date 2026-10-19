// Link probe for a Castlevania-specific upstream game profile plus DS4 bridge.
// NOT the game, no content/assets/recompiled gameplay.
#include <cstdio>
#include <orbis/libkernel.h>
#include <nx/game.h>
#include "platform.h"

int main() {
    setvbuf(stdout, nullptr, _IONBF, 0);
    std::printf("Castlevania PS4: upstream game profile = %s (0x%llx)\n",
                nx::game::kInfo.title,
                static_cast<unsigned long long>(nx::game::kInfo.program_id));
    std::printf("Castlevania PS4: native DS4 bridge initialized; no gameplay linked.\n");
    uint64_t last = 0;
    for (;;) {
        nx::plat::PadState pad{};
        nx::plat::read_pad(pad);
        if (pad.buttons != last) {
            std::printf("Npad buttons: %llx\n", static_cast<unsigned long long>(pad.buttons));
            last = pad.buttons;
        }
        sceKernelUsleep(16667);
    }
}
