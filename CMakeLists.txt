cmake_minimum_required(VERSION 3.16)
project(castlevania_ps4_portworkbench VERSION 0.1.0 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_library(input_adapter STATIC src/input_adapter.cpp)
target_include_directories(input_adapter PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src")
add_executable(test_input tests/test_input.cpp)
target_link_libraries(test_input PRIVATE input_adapter)
enable_testing()
# Kazuma runtime Npad contract - host tests only, not a PS4 build.
add_library(npad_bridge STATIC src/runtime_bridge/npad_bridge.cpp)
target_include_directories(npad_bridge PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_link_libraries(npad_bridge PUBLIC input_adapter)
add_executable(test_npad_bridge tests/test_npad_bridge.cpp)
target_link_libraries(test_npad_bridge PRIVATE npad_bridge)
add_test(NAME test_npad_bridge COMMAND test_npad_bridge)

# Kazuma runtime etapa 2: range checks only, no PS4 API and no game files.
add_library(guest_memory_plan STATIC src/runtime_bridge/guest_memory_plan.cpp)
target_include_directories(guest_memory_plan PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src")
add_executable(test_guest_memory_plan tests/test_guest_memory_plan.cpp)
target_link_libraries(test_guest_memory_plan PRIVATE guest_memory_plan)
add_test(NAME test_guest_memory_plan COMMAND test_guest_memory_plan)

add_test(NAME test_input COMMAND test_input)

# Marca de autoria do trabalho de port — interface estável para o binário PS4.
add_library(kazuma_port_brand STATIC src/runtime_bridge/kazuma_branding.cpp)
target_include_directories(kazuma_port_brand PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src")
add_executable(test_kazuma_branding tests/test_kazuma_branding.cpp)
target_link_libraries(test_kazuma_branding PRIVATE kazuma_port_brand)
add_test(NAME test_kazuma_branding COMMAND test_kazuma_branding)


find_package(Python3 COMPONENTS Interpreter QUIET)
if(Python3_Interpreter_FOUND)
    add_test(NAME switch_audit COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_switch_audit.py")
    add_test(NAME exefs_preflight COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_exefs_preflight.py")
    add_test(NAME exefs_revision COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_exefs_revision.py")
    add_test(NAME exefs_linkage COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_exefs_linkage.py")
    add_test(NAME aot_coverage COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_aot_report_gate.py")
endif()

# Kazuma runtime etapa 3: relogio e sincronizacao testados somente no host.
find_package(Threads REQUIRED)
add_library(time_thread_contract STATIC src/runtime_bridge/time_thread_contract.cpp)
target_include_directories(time_thread_contract PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_link_libraries(time_thread_contract PUBLIC Threads::Threads)
add_executable(test_time_thread_contract tests/test_time_thread_contract.cpp)
target_link_libraries(test_time_thread_contract PRIVATE time_thread_contract)
add_test(NAME test_time_thread_contract COMMAND test_time_thread_contract)
