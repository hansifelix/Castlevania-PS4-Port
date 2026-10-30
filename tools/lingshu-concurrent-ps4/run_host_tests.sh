#!/usr/bin/env bash
# Compile the SAME header as the PS4 bridge with mocked native APIs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CXX="${CXX:-c++}"
"$CXX" -std=c++20 -O1 -g -Wall -Wextra -Werror -pedantic \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I"$ROOT/tools/lingshu-concurrent-ps4" \
  "$ROOT/tools/lingshu-concurrent-ps4/test_concurrent_policy.cpp" \
  -o "$TMP/test-concurrent"
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 "$TMP/test-concurrent"
