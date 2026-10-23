cmake_minimum_required(VERSION 3.16)
project(kazuma65 LANGUAGES C)
# Diagnostico de frame real. Sem jogo, assets comerciais ou ICD simulado.
if(NOT PS4 OR NOT ORBIS_COMPAT_DIR OR NOT ORBIS_SDK_BUNDLE)
  message(FATAL_ERROR "Kazuma65 requer toolchain PS4 e bundle Mesa/RADV reais da etapa 63")
endif()
set(ORBIS_MESA_SRC "${ORBIS_SDK_BUNDLE}/mesa" CACHE PATH "Mesa headers" FORCE)
set(ORBIS_MESA_BUILD "${ORBIS_SDK_BUNDLE}/mesa/build-orbis" CACHE PATH "Mesa compiled driver" FORCE)
find_program(GLSLANG NAMES glslangValidator REQUIRED)
function(kazuma_spv stem)
  add_custom_command(
    OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/tri_${stem}_spv.h"
    COMMAND "${GLSLANG}" -V "${CMAKE_CURRENT_LIST_DIR}/../etapa64/tri.${stem}"
      --vn "tri_${stem}_spv" -o "${CMAKE_CURRENT_BINARY_DIR}/tri_${stem}_spv.h"
    DEPENDS "${CMAKE_CURRENT_LIST_DIR}/../etapa64/tri.${stem}")
endfunction()
kazuma_spv(vert)
kazuma_spv(frag)
add_executable(kazuma65 triangle.c
  "${CMAKE_CURRENT_BINARY_DIR}/tri_vert_spv.h"
  "${CMAKE_CURRENT_BINARY_DIR}/tri_frag_spv.h")
target_include_directories(kazuma65 PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")
if(NOT EXISTS "${ORBIS_SDK_BUNDLE}/orbis-compat/vkloader/CMakeLists.txt")
  message(FATAL_ERROR "Loader Vulkan do bundle nao encontrado")
endif()
add_subdirectory("${ORBIS_SDK_BUNDLE}/orbis-compat/vkloader" "${CMAKE_CURRENT_BINARY_DIR}/ps4-vkloader")
target_link_libraries(kazuma65 PRIVATE ps4-vkloader)
orbis_compat_verify()
if(NOT COMMAND ps4_create_eboot)
  message(FATAL_ERROR "SDK sem ps4_create_eboot")
endif()
ps4_create_eboot(kazuma65)
