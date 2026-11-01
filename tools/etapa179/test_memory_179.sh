#!/usr/bin/env bash
# Real Linux syscalls against the PRODUCTION PS4 memory adapter.
# Host tests do not prove PS4 hardware mapping compatibility.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cat > "$tmp/platform.h" <<'HEADER'
#pragma once
#include <cstdint>
namespace nx::plat {
bool reserve(uint64_t,uint64_t);
bool commit(uint64_t,uint64_t);
void decommit(uint64_t,uint64_t);
}
HEADER
for test in test_decommit_179 test_stress_179; do
    g++ -std=c++20 -O2 -Wall -Wextra -Werror -pthread \
        -I"$tmp" "$root/tools/etapa146/platform_ps4_virtual_memory.cpp" \
        "$root/tools/etapa179/${test}.cpp" -o "$tmp/${test}"
    "$tmp/${test}"
done

# Each failure case starts a new process so a poisoned VM cannot leak
# into another test. --wrap injects failures in real POSIX API calls.
g++ -std=c++20 -O2 -Wall -Wextra -Werror -pthread \
    -Wl,--wrap=madvise -Wl,--wrap=mprotect -Wl,--wrap=munmap \
    -I"$tmp" "$root/tools/etapa146/platform_ps4_virtual_memory.cpp" \
    "$root/tools/etapa179/test_syscall_failures_179.cpp" \
    -o "$tmp/failures"
for case in advice reprotect cleanup commit; do
    "$tmp/failures" "$case"
done

# Force the adapter's logical page size to 16 KiB while using *real*
# Linux syscalls (not a simulated PS4 kernel).
g++ -std=c++20 -O2 -Wall -Wextra -Werror -pthread \
    -Wl,--wrap=sysconf \
    -I"$tmp" "$root/tools/etapa146/platform_ps4_virtual_memory.cpp" \
    "$root/tools/etapa179/test_logical_16k_179.cpp" \
    -o "$tmp/logical-16k"
"$tmp/logical-16k"
