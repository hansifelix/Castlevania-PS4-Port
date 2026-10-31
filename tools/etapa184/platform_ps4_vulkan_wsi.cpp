// Production-oriented Vulkan WSI adapter for the PS4's fullscreen VideoOut.
// Hooks the real vulkan-ps4 ICD's vkGetInstanceProcAddr; no framebuffer draws,
// no fake game frames. Needs the GNM-backed driver linked into final runtime.
// Vulkan KHR_surface does not have a native PS4 window extension. The driver's
// swapchain owns real VideoOut buffers; this shim owns only logical surfaces.
#include "platform.h"
#include <vulkan/vulkan.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <mutex>

extern "C" PFN_vkVoidFunction VKAPI_CALL vkGetInstanceProcAddr(VkInstance, const char*);
extern "C" void lingshu_ps4_set_surface_visible(int);

namespace {
constexpr unsigned kMaxSurfaces=8;
struct Window { uint32_t tag=0x50533457; };
struct Surface { bool active=false; VkInstance instance=VK_NULL_HANDLE; };
Window window;
std::mutex surface_lock;
std::array<Surface,kMaxSurfaces> surfaces{};

bool valid(VkSurfaceKHR handle, VkInstance inst=VK_NULL_HANDLE) {
    if (handle==VK_NULL_HANDLE) return false;
    std::lock_guard<std::mutex> lock(surface_lock);
    for(const Surface& x:surfaces)
        if (reinterpret_cast<VkSurfaceKHR>(const_cast<Surface*>(&x))==handle)
            return x.active && (inst==VK_NULL_HANDLE || x.instance==inst);
    return false;
}
bool attached(VkPhysicalDevice phys,VkSurfaceKHR surface) {
    return phys!=VK_NULL_HANDLE && valid(surface);
}
VkResult size(uint32_t& w,uint32_t& h) {
    nx::plat::desktop_size(w,h);  // real sceVideoOutGetResolutionStatus
    return w>=320 && h>=240 ? VK_SUCCESS : VK_ERROR_SURFACE_LOST_KHR;
}
VkResult report_formats(uint32_t* count,VkSurfaceFormatKHR* values) {
    if (!count) return VK_ERROR_INITIALIZATION_FAILED;
    constexpr VkSurfaceFormatKHR supported[]={
       {VK_FORMAT_B8G8R8A8_UNORM,VK_COLOR_SPACE_SRGB_NONLINEAR_KHR},
       {VK_FORMAT_R8G8B8A8_UNORM,VK_COLOR_SPACE_SRGB_NONLINEAR_KHR},
    };
    constexpr uint32_t n=sizeof(supported)/sizeof(supported[0]);
    if (!values){*count=n;return VK_SUCCESS;}
    const uint32_t written=*count<n?*count:n;
    for(uint32_t i=0;i<written;++i)values[i]=supported[i];
    *count=written;
    return written<n?VK_INCOMPLETE:VK_SUCCESS;
}
}

extern "C" VKAPI_ATTR void VKAPI_CALL
lingshu_vkDestroySurfaceKHR(VkInstance instance,VkSurfaceKHR surface,
                            const VkAllocationCallbacks*) {
    std::lock_guard<std::mutex> lock(surface_lock);
    for(Surface& x:surfaces)
        if (reinterpret_cast<VkSurfaceKHR>(&x)==surface && x.active && x.instance==instance) {
            x.active=false;x.instance=VK_NULL_HANDLE;return;
        }
}
extern "C" VKAPI_ATTR VkResult VKAPI_CALL
lingshu_vkGetPhysicalDeviceSurfaceSupportKHR(VkPhysicalDevice physical,uint32_t family,
                                              VkSurfaceKHR surface,VkBool32* out) {
    if(!out)return VK_ERROR_INITIALIZATION_FAILED;
    *out=VK_FALSE;
    if(!attached(physical,surface))return VK_ERROR_SURFACE_LOST_KHR;
    // The GNM driver uses its graphics/flip queue family 0.
    *out=family==0?VK_TRUE:VK_FALSE;
    return VK_SUCCESS;
}
extern "C" VKAPI_ATTR VkResult VKAPI_CALL
lingshu_vkGetPhysicalDeviceSurfaceCapabilitiesKHR(VkPhysicalDevice physical,VkSurfaceKHR surface,
                                                   VkSurfaceCapabilitiesKHR* caps) {
    if(!caps)return VK_ERROR_INITIALIZATION_FAILED;
    if(!attached(physical,surface))return VK_ERROR_SURFACE_LOST_KHR;
    uint32_t w=0,h=0;const VkResult r=size(w,h);if(r!=VK_SUCCESS)return r;
    *caps={};
    caps->minImageCount=2;caps->maxImageCount=3;
    caps->currentExtent={w,h};caps->minImageExtent={w,h};caps->maxImageExtent={w,h};
    caps->maxImageArrayLayers=1;
    caps->supportedTransforms=VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR;
    caps->currentTransform=VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR;
    caps->supportedCompositeAlpha=VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
    caps->supportedUsageFlags=VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT |
                              VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
    return VK_SUCCESS;
}
extern "C" VKAPI_ATTR VkResult VKAPI_CALL
lingshu_vkGetPhysicalDeviceSurfaceFormatsKHR(VkPhysicalDevice physical,VkSurfaceKHR surface,
                                              uint32_t* count,VkSurfaceFormatKHR* formats) {
    if(!attached(physical,surface))return VK_ERROR_SURFACE_LOST_KHR;
    return report_formats(count,formats);
}
extern "C" VKAPI_ATTR VkResult VKAPI_CALL
lingshu_vkGetPhysicalDeviceSurfacePresentModesKHR(VkPhysicalDevice physical,VkSurfaceKHR surface,
                                                   uint32_t* count,VkPresentModeKHR* modes) {
    if(!attached(physical,surface))return VK_ERROR_SURFACE_LOST_KHR;
    if(!count)return VK_ERROR_INITIALIZATION_FAILED;
    if(!modes){*count=1;return VK_SUCCESS;}
    if(!*count)return VK_INCOMPLETE;
    modes[0]=VK_PRESENT_MODE_FIFO_KHR;
    *count=1;
    return VK_SUCCESS;
}
extern "C" VKAPI_ATTR PFN_vkVoidFunction VKAPI_CALL
lingshu_ps4_vkGetInstanceProcAddr(VkInstance instance,const char* name) {
    if(!name)return nullptr;
    struct Hook {const char* name;PFN_vkVoidFunction fn;};
    constexpr Hook hooks[]={
        {"vkDestroySurfaceKHR",reinterpret_cast<PFN_vkVoidFunction>(&lingshu_vkDestroySurfaceKHR)},
        {"vkGetPhysicalDeviceSurfaceSupportKHR",reinterpret_cast<PFN_vkVoidFunction>(&lingshu_vkGetPhysicalDeviceSurfaceSupportKHR)},
        {"vkGetPhysicalDeviceSurfaceCapabilitiesKHR",reinterpret_cast<PFN_vkVoidFunction>(&lingshu_vkGetPhysicalDeviceSurfaceCapabilitiesKHR)},
        {"vkGetPhysicalDeviceSurfaceFormatsKHR",reinterpret_cast<PFN_vkVoidFunction>(&lingshu_vkGetPhysicalDeviceSurfaceFormatsKHR)},
        {"vkGetPhysicalDeviceSurfacePresentModesKHR",reinterpret_cast<PFN_vkVoidFunction>(&lingshu_vkGetPhysicalDeviceSurfacePresentModesKHR)},
    };
    for(const Hook& hook:hooks) if(std::strcmp(name,hook.name)==0) return hook.fn;
    return vkGetInstanceProcAddr(instance,name);
}

namespace nx::plat {
void* create_window() {
    uint32_t w=0,h=0;
    if(size(w,h)!=VK_SUCCESS){log_line("LINGSHU184: PS4 VideoOut display unavailable");return nullptr;}
    lingshu_ps4_set_surface_visible(1);
    return &window;
}
void release_window(void* w) {
    if(w==&window)lingshu_ps4_set_surface_visible(0);
}
uint64_t window_generation(){return 1;} // No Android-style surface recreation on PS4.
void* vulkan_get_instance_proc_addr(){
    return reinterpret_cast<void*>(&lingshu_ps4_vkGetInstanceProcAddr);
}
const char* vulkan_surface_extension(){
    return VK_KHR_SURFACE_EXTENSION_NAME; // Logical PS4 fullscreen WSI.
}
int vulkan_create_surface(void* instance,void* native_window,
                          uint64_t* surface,void*) {
    if(!instance||!surface||native_window!=&window)return VK_ERROR_INITIALIZATION_FAILED;
    uint32_t w=0,h=0;
    if(size(w,h)!=VK_SUCCESS)return VK_ERROR_SURFACE_LOST_KHR;
    std::lock_guard<std::mutex> lock(surface_lock);
    for(Surface& slot:surfaces)if(!slot.active){
        slot.active=true;slot.instance=reinterpret_cast<VkInstance>(instance);
        *surface=static_cast<uint64_t>(reinterpret_cast<uintptr_t>(&slot));
        return VK_SUCCESS;
    }
    log_line("LINGSHU184: PS4 Vulkan logical surface pool full");
    return VK_ERROR_OUT_OF_HOST_MEMORY;
}
}
