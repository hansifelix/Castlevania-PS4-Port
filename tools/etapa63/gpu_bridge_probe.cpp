// Kazuma Port Games BR - Etapa 63
// Standalone PS4 diagnostic of the *real* nx::plat Vulkan bridge from Etapa 62.
// No game code, no ROMs, no mock ICD, no simulated Vulkan functions.
// Build uses pinned orbis-sdk-v1 (OpenOrbis + Mesa/RADV + Orbis WSI).
#include <orbis_prefix.h>
#include <orbis/libkernel.h>
#include <vulkan/vulkan.h>
#include <cstdint>
#include <cstdio>
#include <cstdarg>
#include <cstring>
#include <unistd.h>

namespace nx::plat {
  void* vulkan_get_instance_proc_addr();
  const char* vulkan_surface_extension();
  int vulkan_create_surface(void*, void*, uint64_t*, void*);
}

namespace nx::plat::ps4 {
// The actual Vulkan loader from the paired Mesa bundle; NOT a fake/mock callback.
void* vk_get_instance_proc_addr() {
  return reinterpret_cast<void*>(&vkGetInstanceProcAddr);
}
}

static void logline(const char* format, ...) {
  char msg[510];
  va_list args;
  va_start(args, format);
  std::vsnprintf(msg, sizeof(msg) - 2, format, args);
  va_end(args);
  std::size_t n = std::strlen(msg);
  if (n < sizeof(msg) - 2) {
    msg[n++] = '\n';
    msg[n] = '\0';
  }
  sceKernelDebugOutText(0, msg);
}
static void idle() {
  for (;;) sleep(1);  // main() returning can look like an unexpected PS4 crash
}
static bool ok(VkResult r, const char* what) {
  logline("KAZUMA63: %s=%s result=%d", what, r==VK_SUCCESS ? "OK" : "FALHOU", int(r));
  return r == VK_SUCCESS;
}

int main() {
  logline("KAZUMA63: BOOT REAL PS4 - SEM JOGO, SEM SHADERS");
  auto gipa = reinterpret_cast<PFN_vkGetInstanceProcAddr>(nx::plat::vulkan_get_instance_proc_addr());
  if (!gipa) { logline("KAZUMA63: GIPA=FALHOU"); idle(); }
  logline("KAZUMA63: GIPA=OK (PROVEDOR MESA/RADV LIGADO)");

  const char* ext[2] = {VK_KHR_SURFACE_EXTENSION_NAME, nx::plat::vulkan_surface_extension()};
  logline("KAZUMA63: EXTENSAO=%s", ext[1]);
  auto create_instance = reinterpret_cast<PFN_vkCreateInstance>(gipa(VK_NULL_HANDLE, "vkCreateInstance"));
  if (!create_instance) { logline("KAZUMA63: vkCreateInstance=SIMBOLO_AUSENTE"); idle(); }
  VkApplicationInfo app{};
  app.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
  app.pApplicationName = "Kazuma Ponte GPU PS4";
  app.apiVersion = VK_API_VERSION_1_1;
  VkInstanceCreateInfo ci{};
  ci.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
  ci.pApplicationInfo = &app;
  ci.enabledExtensionCount = 2;
  ci.ppEnabledExtensionNames = ext;
  VkInstance instance = VK_NULL_HANDLE;
  if (!ok(create_instance(&ci, nullptr, &instance), "INSTANCE")) idle();

  uint64_t raw_surface = 0;
  auto surface_result = static_cast<VkResult>(nx::plat::vulkan_create_surface(
      reinterpret_cast<void*>(instance), nullptr, &raw_surface,
      reinterpret_cast<void*>(gipa)));
  if (!ok(surface_result, "SURFACE")) idle();
  VkSurfaceKHR surface = VK_NULL_HANDLE;
  static_assert(sizeof(surface)==sizeof(raw_surface), "Handle size mismatch");
  std::memcpy(&surface, &raw_surface, sizeof(surface));
  if (surface == VK_NULL_HANDLE) { logline("KAZUMA63: SURFACE=HANDLE_NULO"); idle(); }

  auto enumerate = reinterpret_cast<PFN_vkEnumeratePhysicalDevices>(
      gipa(instance, "vkEnumeratePhysicalDevices"));
  auto properties = reinterpret_cast<PFN_vkGetPhysicalDeviceProperties>(
      gipa(instance, "vkGetPhysicalDeviceProperties"));
  auto get_caps = reinterpret_cast<PFN_vkGetPhysicalDeviceSurfaceCapabilitiesKHR>(
      gipa(instance, "vkGetPhysicalDeviceSurfaceCapabilitiesKHR"));
  if (!enumerate || !properties || !get_caps) {
    logline("KAZUMA63: FUNCOES_GPU=SIMBOLO_AUSENTE"); idle();
  }
  uint32_t count=0;
  if (!ok(enumerate(instance, &count, nullptr), "ENUMERAR_GPU")) idle();
  if (count==0) { logline("KAZUMA63: GPU=NAO_ENCONTRADA"); idle(); }
  VkPhysicalDevice devices[4]{};
  uint32_t wanted = count < 4 ? count : 4;
  if (!ok(enumerate(instance, &wanted, devices), "OBTER_GPU")) idle();
  VkPhysicalDeviceProperties gpu{};
  properties(devices[0], &gpu);
  logline("KAZUMA63: GPU=%s; API=%u.%u; VENDOR=0x%x", gpu.deviceName,
      VK_VERSION_MAJOR(gpu.apiVersion), VK_VERSION_MINOR(gpu.apiVersion), gpu.vendorID);
  VkSurfaceCapabilitiesKHR caps{};
  if (!ok(get_caps(devices[0], surface, &caps), "WSI_CAPS")) idle();
  logline("KAZUMA63: SUPERFICIE=%ux%u; MIN_IMAGES=%u", caps.currentExtent.width,
      caps.currentExtent.height, caps.minImageCount);
  logline("KAZUMA63: PONTE_GPU_REAL=OK; NAO_HA_SWAPCHAIN_NEM_FRAME_NESTA_ETAPA");
  idle();
}
