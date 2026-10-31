// Lingshu etapa 181: native PS4 boot entry with persistent stage diagnostics.
// Actual nx::boot() must only execute after the ORIGINAL AOT/memory checks.
// This is a loader entry, NOT a game binary and NOT a graphics test.
#include "platform.h"
namespace nx { void boot(); }
extern "C" bool lingshu_ps4_guest_layout_valid();
extern "C" bool lingshu_ps4_boot_images_present();

int main() {
    nx::plat::log_line("LINGSHU181_BOOT_ENTRY_STARTED");
    if (!lingshu_ps4_guest_layout_valid()) {
        nx::plat::log_line("LINGSHU181_BOOT_REJECTED_GUEST_LAYOUT");
        return 3;
    }
    nx::plat::log_line("LINGSHU181_GUEST_LAYOUT_CHECKED_NOT_HARDWARE_MAPPED");
    if (!lingshu_ps4_boot_images_present()) {
        nx::plat::log_line("LINGSHU181_BOOT_REJECTED_AOT_IMAGE");
        return 2;
    }
    nx::plat::log_line("LINGSHU181_AOT_IMAGE_VERIFIED_CALLING_REAL_NX_BOOT");
    nx::boot();  // real loader and kernel, never substituted in production
    nx::plat::log_line("LINGSHU181_NX_BOOT_RETURNED_NO_FRAME_ASSERTION");
    return 0;
}
