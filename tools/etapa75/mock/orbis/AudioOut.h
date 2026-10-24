#pragma once
#include <cstdint>
#include <orbis/_types/user.h>
// Mock Linux para validação host; nunca usado no alvo PS4.
extern "C" {
enum OrbisAudioOutPort { ORBIS_AUDIO_OUT_PORT_TYPE_MAIN=0 };
enum OrbisAudioOutParam { ORBIS_AUDIO_OUT_PARAM_FORMAT_S16_STEREO=1 };
int32_t sceAudioOutInit(void);
int32_t sceAudioOutOpen(OrbisUserServiceUserId, OrbisAudioOutPort, int32_t, uint32_t, uint32_t, uint32_t);
int32_t sceAudioOutOutput(int32_t, const void*);
}
