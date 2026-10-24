cmake_minimum_required(VERSION 3.16)
project(kazuma68 LANGUAGES C CXX)
if(NOT PS4 OR NOT ORBIS_COMPAT_DIR OR NOT ORBIS_SDK_BUNDLE)
  message(FATAL_ERROR "Etapa 68 requires real orbis-sdk-v1 PS4 toolchain and Mesa/RADV")
endif()
set(ORBIS_MESA_SRC "${ORBIS_SDK_BUNDLE}/mesa" CACHE PATH "Mesa paired source" FORCE)
set(ORBIS_MESA_BUILD "${ORBIS_SDK_BUNDLE}/mesa/build-orbis" CACHE PATH "Mesa paired build" FORCE)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
find_program(GLSLANG NAMES glslangValidator REQUIRED)
set(ETAPA67 "${CMAKE_CURRENT_LIST_DIR}/../etapa67/triangle.c")
set(ETAPA62 "${CMAKE_CURRENT_LIST_DIR}/../etapa62/ps4_vulkan_bridge.cpp")
if(NOT EXISTS "${ETAPA67}" OR NOT EXISTS "${ETAPA62}")
  message(FATAL_ERROR "Stage 67 and Stage 62 sources must already exist on the build branch")
endif()
add_custom_command(
  OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/triangle68.c"
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/prepare_source.py"
          "${ETAPA67}" "${CMAKE_CURRENT_BINARY_DIR}/triangle68.c"
  DEPENDS "${ETAPA67}" "${CMAKE_CURRENT_LIST_DIR}/prepare_source.py"
  VERBATIM)
function(make_spv stem)
  add_custom_command(
    OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/tri_${stem}_spv.h"
    COMMAND "${GLSLANG}" -V "${CMAKE_CURRENT_LIST_DIR}/../etapa64/tri.${stem}"
            --vn "tri_${stem}_spv" -o "${CMAKE_CURRENT_BINARY_DIR}/tri_${stem}_spv.h"
    DEPENDS "${CMAKE_CURRENT_LIST_DIR}/../etapa64/tri.${stem}"
    VERBATIM)
endfunction()
make_spv(vert)
make_spv(frag)
if(NOT EXISTS "${ORBIS_SDK_BUNDLE}/orbis-compat/vkloader/CMakeLists.txt")
  message(FATAL_ERROR "Missing actual Vulkan loader from paired SDK bundle")
endif()
add_subdirectory("${ORBIS_SDK_BUNDLE}/orbis-compat/vkloader"
  "${CMAKE_CURRENT_BINARY_DIR}/ps4-vkloader")
add_executable(kazuma68
  "${CMAKE_CURRENT_BINARY_DIR}/triangle68.c"
  "${CMAKE_CURRENT_LIST_DIR}/bridge_gpu.cpp"
  "${ETAPA62}"
  "${CMAKE_CURRENT_BINARY_DIR}/tri_vert_spv.h"
  "${CMAKE_CURRENT_BINARY_DIR}/tri_frag_spv.h")
target_include_directories(kazuma68 PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")
set_target_properties(kazuma68 PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED YES)
target_link_libraries(kazuma68 PRIVATE ps4-vkloader)
orbis_compat_verify()
if(NOT COMMAND ps4_create_eboot)
  message(FATAL_ERROR "Missing ps4_create_eboot")
endif()
ps4_create_eboot(kazuma68)
