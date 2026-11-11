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
