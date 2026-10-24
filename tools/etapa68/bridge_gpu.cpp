// Kazuma 68: real nx::plat API -> the same Mesa/RADV + Orbis WSI as Etapa 67.
// No fake Vulkan symbols, Nintendo binary, game resources or original gameplay.
#include <orbis_prefix.h>
#include <vulkan/vulkan.h>
#include <cstdint>
#include <cstring>

namespace nx::plat {
    void* vulkan_get_instance_proc_addr();
    const char* vulkan_surface_extension();
    int vulkan_create_surface(void*, void*, uint64_t*, void*);
}
namespace nx::plat::ps4 {
void* vk_get_instance_proc_addr() {
    return reinterpret_cast<void*>(&vkGetInstanceProcAddr);
}
}
extern "C" void* kazuma68_gipa(void) {
    return nx::plat::vulkan_get_instance_proc_addr();
}
extern "C" const char* kazuma68_surface_extension(void) {
    return nx::plat::vulkan_surface_extension();
}
extern "C" int kazuma68_create_surface(VkInstance instance, VkSurfaceKHR* surface_out) {
    if (!instance || !surface_out) return VK_ERROR_INITIALIZATION_FAILED;
    *surface_out = VK_NULL_HANDLE;
    uint64_t raw_surface = 0;
    const int result = nx::plat::vulkan_create_surface(
        reinterpret_cast<void*>(instance), nullptr, &raw_surface,
        nx::plat::vulkan_get_instance_proc_addr());
    if (result == VK_SUCCESS) {
        static_assert(sizeof(VkSurfaceKHR) == sizeof(raw_surface),
                      "Expected 64-bit Vulkan surface handle");
        std::memcpy(surface_out, &raw_surface, sizeof(raw_surface));
    }
    return result;
}
