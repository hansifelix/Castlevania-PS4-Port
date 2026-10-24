// Provider concreto do ponte Vulkan Publica Etapa 62.
// vkGetInstanceProcAddr e um import REAL da vkloader/Mesa PS4, NAO um mock.
// O link estrito podera falhar ate que a biblioteca real seja adicionada.
#include <vulkan/vulkan.h>
namespace nx::plat::ps4 {
void* vk_get_instance_proc_addr() {
    return reinterpret_cast<void*>(&vkGetInstanceProcAddr);
}
}
