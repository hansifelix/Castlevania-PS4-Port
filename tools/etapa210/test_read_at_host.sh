#!/usr/bin/env bash
# Exercise real production POSIX loader read_at with a real tempfile and
# a wrapped pread syscall; no copyrighted assets, no PS4 hardware claim.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cat > "$tmp/platform.h" <<'HEADER'
#pragma once
#include <cstdint>
#include <cstdio>
namespace nx::plat {
uint64_t read_at(FILE* file, int64_t offset, void* dest, uint64_t len);
}
HEADER

g++ -std=c++20 -O2 -Wall -Wextra -Werror -pthread -fsanitize=undefined \
    -Wl,--wrap=pread \
    -I"$tmp" "$root/tools/etapa144/platform_ps4_posix_core.cpp" \
    "$root/tools/etapa210/test_read_at_host.cpp" -o "$tmp/read-at-test"
"$tmp/read-at-test"
