// Mock signatures ONLY for Linux; never link these with PS4 executable.
#pragma once
#include <cstddef>
#include <cstdint>
extern "C" std::int32_t sceKernelReserveVirtualRange(void**,std::size_t,std::int32_t,std::size_t);
extern "C" std::int32_t sceKernelMunmap(void*,std::size_t);
extern "C" int sceKernelUsleep(unsigned);
