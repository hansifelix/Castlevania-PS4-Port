// Testes executam em Linux com mock declarado; não testam áudio em PS4.
#include <orbis/AudioOut.h>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
#include <algorithm>
namespace nx::plat {
using AudioDone = void (*)(void*);
bool audio_open(AudioDone);
bool audio_submit(const void*, size_t, void*);
uint32_t audio_queued();
}
static int init_calls=0,open_calls=0,chunk_calls=0,barriers=0,completed=0;
static bool fail_output=false;
static std::vector<uint8_t> submitted;
extern "C" {
int32_t sceAudioOutInit() { ++init_calls; return 0; }
int32_t sceAudioOutOpen(OrbisUserServiceUserId user,OrbisAudioOutPort port,int32_t, uint32_t frames, uint32_t rate, uint32_t format) {
    assert(user==ORBIS_USER_SERVICE_USER_ID_SYSTEM);
    assert(port==ORBIS_AUDIO_OUT_PORT_TYPE_MAIN);
    assert(frames==256 && rate==48000 && format==ORBIS_AUDIO_OUT_PARAM_FORMAT_S16_STEREO);
    ++open_calls;return 7;
}
int32_t sceAudioOutOutput(int32_t handle,const void* buf) {
    assert(handle==7);
    if (fail_output) return -1;
    if (!buf) { ++barriers; return 0; }
    ++chunk_calls;
    auto* p=static_cast<const uint8_t*>(buf);
    submitted.insert(submitted.end(),p,p+1024);
    return 0;
}
}
static void done(void* ctx){assert(ctx == &completed);++completed;assert(nx::plat::audio_queued()==0);}
int main() {
    assert(nx::plat::audio_queued()==0);
    assert(!nx::plat::audio_submit("1234",4,&completed));
    assert(nx::plat::audio_open(done));
    assert(init_calls==1 && open_calls==1);
    assert(nx::plat::audio_open(done));
    assert(init_calls==1 && open_calls==1);
    std::vector<uint8_t> data(1028);
    for(size_t i=0;i<data.size();++i) data[i]=static_cast<uint8_t>(i%251);
    assert(nx::plat::audio_submit(data.data(),data.size(),&completed));
    assert(chunk_calls==2 && barriers==1 && completed==1);
    assert(std::equal(data.begin(),data.end(),submitted.begin()));
    for(size_t i=data.size();i<submitted.size();++i) assert(submitted[i]==0);
    assert(!nx::plat::audio_submit(data.data(),3,&completed));
    fail_output=true;
    assert(!nx::plat::audio_submit(data.data(),4,&completed));
    assert(completed==1 && nx::plat::audio_queued()==0);
    fail_output=false;
    assert(nx::plat::audio_submit(nullptr,0,&completed));
    assert(completed==2);
    puts("KAZUMA75 HOST: audio S16 48kHz, padding, callback, erro e fila = PASSOU (MOCK Linux)");
}
