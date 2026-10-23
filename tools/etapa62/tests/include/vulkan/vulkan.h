#pragma once
// Só para teste de interface no Termux; NÃO usar para compilar o PKG PS4.
#include <cstdint>
#define VK_NULL_HANDLE 0
#define VK_EXT_HEADLESS_SURFACE_EXTENSION_NAME "VK_EXT_headless_surface"
#define VK_STRUCTURE_TYPE_HEADLESS_SURFACE_CREATE_INFO_EXT 1000256000
#define VK_SUCCESS 0
#define VK_ERROR_INITIALIZATION_FAILED (-3)
#define VK_ERROR_EXTENSION_NOT_PRESENT (-7)
#define VKAPI_PTR
using VkInstance = void*;
using VkSurfaceKHR = uint64_t;
using VkResult = int32_t;
struct VkAllocationCallbacks;
using PFN_vkVoidFunction = void(VKAPI_PTR *)();
using PFN_vkGetInstanceProcAddr = PFN_vkVoidFunction(VKAPI_PTR *)(VkInstance, const char*);
struct VkHeadlessSurfaceCreateInfoEXT {
    int32_t sType;
    const void* pNext;
    uint32_t flags;
};
using PFN_vkCreateHeadlessSurfaceEXT = VkResult(VKAPI_PTR *)(VkInstance, const VkHeadlessSurfaceCreateInfoEXT*, const VkAllocationCallbacks*, VkSurfaceKHR*);
