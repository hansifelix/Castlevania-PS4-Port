// Host contract of the real PS4 Vulkan WSI bridge. NO GPU hardware, game,
// shaders, render buffers or fake game image. Desktop resolution is simulated
// only so the underlying WSI API logic can be tested deterministically.
#include "platform.h"
#include <vulkan/vulkan.h>
#include <cstdio>
#include <cstdint>
#include <cstring>

namespace {
unsigned g_w=1920,g_h=1080;
bool g_visible=false;
int g_delegations=0;
}
namespace nx::plat {
void desktop_size(uint32_t& w,uint32_t& h){w=g_w;h=g_h;}
void log_line(const char*){}
}
extern "C" void lingshu_ps4_set_surface_visible(int v){g_visible=v!=0;}
extern "C" void VKAPI_CALL fake_vk_entry() {}
extern "C" PFN_vkVoidFunction VKAPI_CALL vkGetInstanceProcAddr(VkInstance,const char* name){
    if(name && std::strcmp(name,"vkCreateInstance")==0) {++g_delegations;return &fake_vk_entry;}
    return nullptr;
}
extern "C" PFN_vkVoidFunction VKAPI_CALL lingshu_ps4_vkGetInstanceProcAddr(VkInstance,const char*);
extern "C" void VKAPI_CALL lingshu_vkDestroySurfaceKHR(VkInstance,VkSurfaceKHR,const VkAllocationCallbacks*);
extern "C" VkResult VKAPI_CALL lingshu_vkGetPhysicalDeviceSurfaceSupportKHR(VkPhysicalDevice,uint32_t,VkSurfaceKHR,VkBool32*);
extern "C" VkResult VKAPI_CALL lingshu_vkGetPhysicalDeviceSurfaceCapabilitiesKHR(VkPhysicalDevice,VkSurfaceKHR,VkSurfaceCapabilitiesKHR*);
extern "C" VkResult VKAPI_CALL lingshu_vkGetPhysicalDeviceSurfaceFormatsKHR(VkPhysicalDevice,VkSurfaceKHR,uint32_t*,VkSurfaceFormatKHR*);
extern "C" VkResult VKAPI_CALL lingshu_vkGetPhysicalDeviceSurfacePresentModesKHR(VkPhysicalDevice,VkSurfaceKHR,uint32_t*,VkPresentModeKHR*);
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"LINGSHU184_WSI_ERROR line=%d expr=%s\n",__LINE__,#x);return 1;}}while(0)
int main() {
    VkInstance instance=reinterpret_cast<VkInstance>(uintptr_t(0x4111));
    VkPhysicalDevice gpu=reinterpret_cast<VkPhysicalDevice>(uintptr_t(0x4222));
    CHECK(nx::plat::vulkan_get_instance_proc_addr());
    const char* extension=nx::plat::vulkan_surface_extension();
    CHECK(extension && std::strcmp(extension,VK_KHR_SURFACE_EXTENSION_NAME)==0);
    CHECK(lingshu_ps4_vkGetInstanceProcAddr(instance,"vkGetPhysicalDeviceSurfaceFormatsKHR")!=nullptr);
    CHECK(lingshu_ps4_vkGetInstanceProcAddr(instance,"vkGetPhysicalDeviceSurfaceSupportKHR")!=nullptr);
    CHECK(lingshu_ps4_vkGetInstanceProcAddr(instance,"vkGetPhysicalDeviceSurfaceCapabilitiesKHR")!=nullptr);
    CHECK(lingshu_ps4_vkGetInstanceProcAddr(instance,"vkGetPhysicalDeviceSurfacePresentModesKHR")!=nullptr);
    CHECK(lingshu_ps4_vkGetInstanceProcAddr(instance,"vkDestroySurfaceKHR")!=nullptr);
    CHECK(lingshu_ps4_vkGetInstanceProcAddr(instance,"vkCreateInstance")!=nullptr && g_delegations==1);
    CHECK(!lingshu_ps4_vkGetInstanceProcAddr(instance,"vkBadNonexistent"));
    void* win=nx::plat::create_window();
    CHECK(win && g_visible && nx::plat::window_generation()==1);
    uint64_t raw=0;
    CHECK(nx::plat::vulkan_create_surface(instance,win,&raw,nullptr)==VK_SUCCESS);
    CHECK(raw!=0);
    VkSurfaceKHR surface=reinterpret_cast<VkSurfaceKHR>(uintptr_t(raw));
    VkBool32 support=VK_FALSE;
    CHECK(lingshu_vkGetPhysicalDeviceSurfaceSupportKHR(gpu,0,surface,&support)==VK_SUCCESS && support==VK_TRUE);
    CHECK(lingshu_vkGetPhysicalDeviceSurfaceSupportKHR(gpu,1,surface,&support)==VK_SUCCESS && support==VK_FALSE);
    VkSurfaceCapabilitiesKHR caps{};
    CHECK(lingshu_vkGetPhysicalDeviceSurfaceCapabilitiesKHR(gpu,surface,&caps)==VK_SUCCESS);
    CHECK(caps.currentExtent.width==1920 && caps.currentExtent.height==1080);
    CHECK(caps.minImageCount==2 && caps.maxImageCount==3);
    uint32_t count=0;
    CHECK(lingshu_vkGetPhysicalDeviceSurfaceFormatsKHR(gpu,surface,&count,nullptr)==VK_SUCCESS&&count==2);
    VkSurfaceFormatKHR formats[2]{};
    count=1;
    CHECK(lingshu_vkGetPhysicalDeviceSurfaceFormatsKHR(gpu,surface,&count,formats)==VK_INCOMPLETE && count==1);
    CHECK(formats[0].format==VK_FORMAT_B8G8R8A8_UNORM);
    count=2;
    CHECK(lingshu_vkGetPhysicalDeviceSurfaceFormatsKHR(gpu,surface,&count,formats)==VK_SUCCESS&&count==2);
    count=0;
    CHECK(lingshu_vkGetPhysicalDeviceSurfacePresentModesKHR(gpu,surface,&count,nullptr)==VK_SUCCESS&&count==1);
    VkPresentModeKHR mode{};
    CHECK(lingshu_vkGetPhysicalDeviceSurfacePresentModesKHR(gpu,surface,&count,&mode)==VK_SUCCESS&&mode==VK_PRESENT_MODE_FIFO_KHR);
    g_w=0;
    CHECK(lingshu_vkGetPhysicalDeviceSurfaceCapabilitiesKHR(gpu,surface,&caps)==VK_ERROR_SURFACE_LOST_KHR);
    CHECK(nx::plat::vulkan_create_surface(instance,win,&raw,nullptr)==VK_ERROR_SURFACE_LOST_KHR);
    g_w=1920;
    lingshu_vkDestroySurfaceKHR(instance,surface,nullptr);
    CHECK(lingshu_vkGetPhysicalDeviceSurfaceCapabilitiesKHR(gpu,surface,&caps)==VK_ERROR_SURFACE_LOST_KHR);
    CHECK(nx::plat::vulkan_create_surface(instance,win,&raw,nullptr)==VK_SUCCESS);
    nx::plat::release_window(win);
    CHECK(!g_visible);
    std::puts("LINGSHU184_PS4_VULKAN_WSI_HOST=PASSED_24_CONTRACTS_NO_GPU_NO_GAME");
}
