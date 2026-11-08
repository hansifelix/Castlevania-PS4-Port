// Real loader hook for the public NVN -> Vulkan PS4 bridge.
// Must be linked with the paired orbis-ports Mesa/RADV vkloader bundle.
// The PS4 OpenOrbis SDK alone does NOT provide this Vulkan implementation.
// Do not replace vkGetInstanceProcAddr with a null/no-op shim.
#ifndef KAZUMA_PS4_REAL_VULKAN
#error "Only enable this provider when linking an actual PS4 Mesa/RADV vkloader"
#endif
#ifdef VK_NO_PROTOTYPES
#error "Real vkGetInstanceProcAddr declaration is required"
#endif
#include <vulkan/vulkan.h>

namespace nx::plat::ps4 {
void* vk_get_instance_proc_addr() {
    // Direct relocation to the actual external vkloader. A partial link
    // must retain the unresolved vkGetInstanceProcAddr import until the
    // paired Mesa/RADV build supplies the genuine implementation.
    return reinterpret_cast<void*>(&::vkGetInstanceProcAddr);
}
} // namespace nx::plat::ps4
