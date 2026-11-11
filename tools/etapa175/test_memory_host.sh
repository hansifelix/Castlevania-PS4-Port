#!/usr/bin/env bash
# LINGSHU175 - test original virtual-memory PS4 adapter on Linux with the
# real mmap/mprotect syscalls. No game and NO simulated implementation.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cat > "$tmp/platform.h" <<'HEADER'
#pragma once
#include <cstdint>
namespace nx::plat {
bool reserve(uint64_t addr, uint64_t size);
bool commit(uint64_t addr, uint64_t size);
void decommit(uint64_t addr, uint64_t size);
}
HEADER
cat > "$tmp/test.cpp" <<'CPP'
#include "platform.h"
#include <sys/mman.h>
#include <unistd.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>

#define CHECK(value) do { if (!(value)) { std::fprintf(stderr, "FAILED: %s at line %d\n", #value, __LINE__); return 1; } } while(0)
int main() {
    using namespace nx::plat;
    const long sys_page=sysconf(_SC_PAGESIZE);
    CHECK(sys_page>0 && (sys_page & (sys_page-1)) == 0);
    const uint64_t page=static_cast<uint64_t>(sys_page);
    const size_t bytes=static_cast<size_t>(page*4);
    int cases=0;
    auto ok=[&](bool v){CHECK(v);++cases; return 0;};
    // Ask the OS for a good address, unmap, then test exactly that address.
    // No MAP_FIXED on the production adapter: existing mappings must survive.
    void* suggestion=mmap(nullptr,bytes,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    CHECK(suggestion!=MAP_FAILED);
    const uint64_t base=reinterpret_cast<uintptr_t>(suggestion);
    CHECK(munmap(suggestion,bytes)==0);
    CHECK(ok(reserve(base,bytes))==0);
    CHECK(ok(!reserve(base+page,page))==0);              // no double-reserve
    CHECK(ok(!reserve(base,page))==0);                   // no overlap
    CHECK(ok(!commit(base+bytes,page))==0);              // outside reserve
    CHECK(ok(!commit(base+3*page,2*page))==0);          // straddling end
    CHECK(ok(!commit(UINT64_MAX-1024,4096))==0);        // overflow fail-closed
    CHECK(ok(!reserve(UINT64_MAX-1024,4096))==0);       // invalid region
    CHECK(ok(commit(base,bytes))==0);
    auto* memory=reinterpret_cast<unsigned char*>(static_cast<uintptr_t>(base));
    std::memset(memory,0x5a,bytes);
    // Correct behavior: only the selected page is decommitted.
    decommit(base+page,page);
    CHECK(ok(commit(base+page,page))==0);
    CHECK(ok(memory[0]==0x5a && memory[page]==0 && memory[2*page]==0x5a)==0);
    // An unaligned decommit must keep neighboring bytes on a shared page.
    decommit(base+2*page+20,33);
    CHECK(ok(memory[2*page+19]==0x5a && memory[2*page+20]==0 &&
             memory[2*page+52]==0 && memory[2*page+53]==0x5a)==0);
    // The mapping must remain usable by commit after decommit.
    decommit(base+3*page,page);
    CHECK(ok(commit(base+3*page,page))==0);
    CHECK(ok(memory[3*page]==0)==0);
    // Never evict unrelated host memory with a fixed-map operation.
    void* unrelated=mmap(nullptr,static_cast<size_t>(page),PROT_READ|PROT_WRITE,
                         MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    CHECK(unrelated!=MAP_FAILED);
    auto* byte=static_cast<unsigned char*>(unrelated);
    byte[0]=0xa7;
    CHECK(ok(!reserve(reinterpret_cast<uintptr_t>(unrelated),page))==0);
    CHECK(ok(byte[0]==0xa7)==0);
    CHECK(munmap(unrelated,static_cast<size_t>(page))==0);
    CHECK(munmap(reinterpret_cast<void*>(static_cast<uintptr_t>(base)),bytes)==0);
    std::printf("LINGSHU175_PS4_MEMORY_HOST_REGRESSION=PASSED_%d_CASES_NO_GAME\n",cases);
    return 0;
}
CPP
g++ -std=c++20 -O2 -Wall -Wextra -Werror -pthread \
    -I"$tmp" "$root/tools/etapa146/platform_ps4_virtual_memory.cpp" \
    "$tmp/test.cpp" -o "$tmp/memory-check"
"$tmp/memory-check"
