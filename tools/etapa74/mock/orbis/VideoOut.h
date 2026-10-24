// Host-only mock of the subset of the OpenOrbis ABI required in this test.
#pragma once
#include <cstdint>
#define ORBIS_VIDEO_USER_MAIN 0xFF
#define ORBIS_VIDEO_OUT_BUS_MAIN 0
struct OrbisVideoOutResolutionStatus {
    uint32_t width, height, paneWidth, paneHeight;
    uint64_t refreshRate;
    float screenSize;
    uint16_t flags, reserved0;
    uint32_t reserved1[3];
};
extern "C" {
int32_t sceVideoOutOpen(int32_t, int32_t, int32_t, const void*);
int32_t sceVideoOutGetResolutionStatus(int32_t, OrbisVideoOutResolutionStatus*);
int32_t sceVideoOutClose(int32_t);
}
