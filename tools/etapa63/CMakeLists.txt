cmake_minimum_required(VERSION 3.16)
project(kazuma_etapa63 LANGUAGES C CXX)

# There is no reasonable non-PS4 fallback; a native Linux build would be misleading.
if(NOT PS4 OR NOT ORBIS_COMPAT_DIR OR NOT ORBIS_SDK_BUNDLE)
  message(FATAL_ERROR "Required: the genuine pinned orbis-sdk-v1 PS4 CMake toolchain")
endif()
if(NOT EXISTS "${ORBIS_SDK_BUNDLE}/orbis-compat/vkloader/CMakeLists.txt")
  message(FATAL_ERROR "The pinned SDK bundle is missing its real ps4-vkloader")
endif()

# Use the actual Mesa/RADV loader and its paired Vulkan headers. No fake ICD or stubs.
set(ORBIS_MESA_SRC "${ORBIS_SDK_BUNDLE}/mesa" CACHE PATH "Paired Mesa" FORCE)
set(ORBIS_MESA_BUILD "${ORBIS_SDK_BUNDLE}/mesa/build-orbis" CACHE PATH "Paired RADV archive" FORCE)
add_subdirectory("${ORBIS_SDK_BUNDLE}/orbis-compat/vkloader" "${CMAKE_CURRENT_BINARY_DIR}/ps4-vkloader")

add_executable(kazuma63
  gpu_bridge_probe.cpp
  "${CMAKE_CURRENT_LIST_DIR}/../../tools/etapa62/ps4_vulkan_bridge.cpp")
set_target_properties(kazuma63 PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED YES)
target_link_libraries(kazuma63 PRIVATE ps4-vkloader)
orbis_compat_verify()
if(NOT COMMAND ps4_create_eboot)
  message(FATAL_ERROR "SDK does not supply ps4_create_eboot")
endif()
ps4_create_eboot(kazuma63)
