// Kazuma Port Games BR - contrato de superficie NVN -> Vulkan para PS4.
// Usa as assinaturas nx::plat do runtime publico. Este arquivo NAO substitui o
// driver Mesa, o WSI PS4 nem o VideoOut; nao cria nem apresenta frames sozinho.
// Compilar contra os cabecalhos Vulkan REAIS para alvo PS4 na CI da etapa 62.
#define VK_NO_PROTOTYPES
#include <vulkan/vulkan.h>
#include <cstdint>
#include <cstring>

namespace nx::plat::ps4 {
// Dependencia intencional: futura implementacao Mesa/RADV + WSI para PS4.
// NAO fornecer corpo simulado em uma build instalavel no PS4.
void* vk_get_instance_proc_addr();
}

namespace nx::plat {

void* vulkan_get_instance_proc_addr() {
    return ps4::vk_get_instance_proc_addr();
}

const char* vulkan_surface_extension() {
    return VK_EXT_HEADLESS_SURFACE_EXTENSION_NAME;
}

int vulkan_create_surface(void* instance, void* native_window,
                          uint64_t* surface_out, void* gipa_address) {
    (void)native_window;  // Surface headless: o VideoOut pertence ao WSI PS4.
    if (!surface_out || !instance) return VK_ERROR_INITIALIZATION_FAILED;
    *surface_out = 0;

    void* addr = gipa_address ? gipa_address : vulkan_get_instance_proc_addr();
    if (!addr) return VK_ERROR_INITIALIZATION_FAILED;
    auto get_proc = reinterpret_cast<PFN_vkGetInstanceProcAddr>(addr);
    auto create = reinterpret_cast<PFN_vkCreateHeadlessSurfaceEXT>(
        get_proc(reinterpret_cast<VkInstance>(instance), "vkCreateHeadlessSurfaceEXT"));
    if (!create) return VK_ERROR_EXTENSION_NOT_PRESENT;

    VkHeadlessSurfaceCreateInfoEXT ci{};
    ci.sType = VK_STRUCTURE_TYPE_HEADLESS_SURFACE_CREATE_INFO_EXT;
    VkSurfaceKHR surface = VK_NULL_HANDLE;
    const auto r = create(reinterpret_cast<VkInstance>(instance), &ci, nullptr, &surface);
    if (r == VK_SUCCESS) {
        static_assert(sizeof(VkSurfaceKHR) == sizeof(uint64_t),
                      "PS4 x86-64: VkSurfaceKHR precisa caber em 64 bits");
        std::memcpy(surface_out, &surface, sizeof(surface));
    }
    return r;
}
}  // namespace nx::plat
