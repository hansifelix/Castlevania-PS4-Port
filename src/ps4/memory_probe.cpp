#include "memory_probe.h"

#include <cerrno>
#include <sys/mman.h>

namespace cvps4 {
namespace {
constexpr std::size_t kMaxProbeBytes = 1024u * 1024u;
#if defined(MAP_ANONYMOUS)
constexpr int kAnonymous = MAP_ANONYMOUS;
#elif defined(MAP_ANON)
constexpr int kAnonymous = MAP_ANON;
#else
#error "Este ambiente nao fornece MAP_ANON nem MAP_ANONYMOUS"
#endif
}

MemoryProbeResult check_anonymous_mapping(std::size_t bytes) {
    if (bytes == 0 || bytes > kMaxProbeBytes) {
        return {ProbeStage::invalid_size, 0, 0, bytes};
    }

    // O kernel escolhe o endereco. PROT_NONE evita acesso ate mprotect ser validado.
    void* p = mmap(nullptr, bytes, PROT_NONE, MAP_PRIVATE | kAnonymous, -1, 0);
    if (p == MAP_FAILED) {
        return {ProbeStage::mmap_failed, errno, 0, bytes};
    }

    const auto address = reinterpret_cast<std::uintptr_t>(p);
    if (mprotect(p, bytes, PROT_READ | PROT_WRITE) != 0) {
        const int e = errno;
        (void)munmap(p, bytes);
        return {ProbeStage::mprotect_failed, e, address, bytes};
    }

    volatile unsigned char* const data = static_cast<volatile unsigned char*>(p);
    data[0] = 0x5A;
    data[bytes - 1] = 0xC3;
    const bool match = data[0] == (bytes == 1 ? 0xC3 : 0x5A) && data[bytes - 1] == 0xC3;
    if (munmap(p, bytes) != 0) {
        return {ProbeStage::munmap_failed, errno, address, bytes};
    }
    return {match ? ProbeStage::ok : ProbeStage::data_mismatch, 0, address, bytes};
}

const char* probe_stage_name(ProbeStage stage) {
    switch (stage) {
        case ProbeStage::ok: return "ok";
        case ProbeStage::invalid_size: return "invalid_size";
        case ProbeStage::mmap_failed: return "mmap_failed";
        case ProbeStage::mprotect_failed: return "mprotect_failed";
        case ProbeStage::data_mismatch: return "data_mismatch";
        case ProbeStage::munmap_failed: return "munmap_failed";
    }
    return "unknown";
}
} // namespace cvps4
