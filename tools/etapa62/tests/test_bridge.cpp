#include <cassert>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <string>
#include <vulkan/vulkan.h>

namespace nx::plat {
void* vulkan_get_instance_proc_addr();
const char* vulkan_surface_extension();
int vulkan_create_surface(void*,void*,uint64_t*,void*);
}
static int calls = 0;
static bool has_extension = true, fail_create = false;
static VkResult fake_create(VkInstance, const VkHeadlessSurfaceCreateInfoEXT* info,
                            const VkAllocationCallbacks*, VkSurfaceKHR* out) {
    ++calls;
    assert(info->sType == VK_STRUCTURE_TYPE_HEADLESS_SURFACE_CREATE_INFO_EXT);
    if (fail_create) return VK_ERROR_INITIALIZATION_FAILED;
    *out = 0xCA5E1234u;
    return VK_SUCCESS;
}
static PFN_vkVoidFunction fake_get(VkInstance, const char* name) {
    assert(std::string(name) == "vkCreateHeadlessSurfaceEXT");
    return has_extension ? reinterpret_cast<PFN_vkVoidFunction>(&fake_create) : nullptr;
}
static void* func_address(PFN_vkGetInstanceProcAddr fn) {
    static_assert(sizeof(fn)==sizeof(void*));
    void* out=nullptr;
    std::memcpy(&out, &fn, sizeof(fn));
    return out;
}
namespace nx::plat::ps4 {
void* vk_get_instance_proc_addr() { return func_address(fake_get); }
}
int main() {
    using namespace nx::plat;
    assert(std::string(vulkan_surface_extension()) == "VK_EXT_headless_surface");
    assert(vulkan_get_instance_proc_addr()!=nullptr);
    uint64_t surf=55;
    assert(vulkan_create_surface(nullptr,nullptr,&surf,nullptr) == VK_ERROR_INITIALIZATION_FAILED);
    assert(vulkan_create_surface(reinterpret_cast<void*>(1),nullptr,nullptr,nullptr) == VK_ERROR_INITIALIZATION_FAILED);
    has_extension = false;
    assert(vulkan_create_surface(reinterpret_cast<void*>(1),nullptr,&surf,nullptr) == VK_ERROR_EXTENSION_NOT_PRESENT);
    assert(surf == 0);
    has_extension = true;
    fail_create = true;
    assert(vulkan_create_surface(reinterpret_cast<void*>(1),nullptr,&surf,nullptr) == VK_ERROR_INITIALIZATION_FAILED);
    assert(surf == 0);
    fail_create = false;
    assert(vulkan_create_surface(reinterpret_cast<void*>(1),nullptr,&surf,func_address(fake_get)) == VK_SUCCESS);
    assert(surf == 0xCA5E1234u);
    assert(calls == 2);
    std::puts("KAZUMA62: CONTRATO_VULKAN=OK (SIMULADO; SEM GPU PS4)");
}
