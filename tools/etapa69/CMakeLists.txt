cmake_minimum_required(VERSION 3.16)
project(kazuma69 LANGUAGES C CXX)
if(NOT PS4 OR NOT ORBIS_COMPAT_DIR OR NOT ORBIS_SDK_BUNDLE)
 message(FATAL_ERROR "Requires real PS4 orbis-sdk-v1 / Mesa bundle")
endif()
set(ORBIS_MESA_SRC "${ORBIS_SDK_BUNDLE}/mesa" CACHE PATH "Mesa src" FORCE)
set(ORBIS_MESA_BUILD "${ORBIS_SDK_BUNDLE}/mesa/build-orbis" CACHE PATH "Mesa RADV" FORCE)
find_program(GLSLANG glslangValidator REQUIRED)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(R68 "${CMAKE_CURRENT_BINARY_DIR}/triangle68.c")
set(R69 "${CMAKE_CURRENT_BINARY_DIR}/elephant69.c")
add_custom_command(OUTPUT "${R68}"
 COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/../etapa68/prepare_source.py"
 "${CMAKE_CURRENT_LIST_DIR}/../etapa67/triangle.c" "${R68}"
 DEPENDS "${CMAKE_CURRENT_LIST_DIR}/../etapa68/prepare_source.py"
 "${CMAKE_CURRENT_LIST_DIR}/../etapa67/triangle.c"
 VERBATIM)
add_custom_command(OUTPUT "${R69}"
 COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/prepare_source.py"
 "${R68}" "${R69}"
 DEPENDS "${R68}" "${CMAKE_CURRENT_LIST_DIR}/prepare_source.py"
 VERBATIM)
foreach(phase IN ITEMS vert frag)
 add_custom_command(OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/elephant_${phase}_spv.h"
  COMMAND "${GLSLANG}" -V "${CMAKE_CURRENT_LIST_DIR}/elephant.${phase}"
  --vn "elephant_${phase}_spv" -o "${CMAKE_CURRENT_BINARY_DIR}/elephant_${phase}_spv.h"
  DEPENDS "${CMAKE_CURRENT_LIST_DIR}/elephant.${phase}"
  VERBATIM)
endforeach()
add_subdirectory("${ORBIS_SDK_BUNDLE}/orbis-compat/vkloader"
 "${CMAKE_CURRENT_BINARY_DIR}/ps4-vkloader")
add_executable(kazuma69
 "${R69}"
 "${CMAKE_CURRENT_LIST_DIR}/gameplay.c"
 "${CMAKE_CURRENT_LIST_DIR}/bridge_gpu_link.cpp"
 "${CMAKE_CURRENT_LIST_DIR}/../etapa62/ps4_vulkan_bridge.cpp"
 "${CMAKE_CURRENT_BINARY_DIR}/elephant_vert_spv.h"
 "${CMAKE_CURRENT_BINARY_DIR}/elephant_frag_spv.h")
target_include_directories(kazuma69 PRIVATE "${CMAKE_CURRENT_BINARY_DIR}" "${CMAKE_CURRENT_LIST_DIR}")
target_link_libraries(kazuma69 PRIVATE ps4-vkloader -lScePad -lSceUserService -lm)
orbis_compat_verify()
if(NOT COMMAND ps4_create_eboot)
 message(FATAL_ERROR "SDK missing ps4_create_eboot")
endif()
ps4_create_eboot(kazuma69)
