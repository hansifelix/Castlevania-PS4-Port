#!/usr/bin/env bash
# Stage207: same C++ probe policy as PS4 bridge, simulated native call outputs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CXX="${CXX:-c++}"
"$CXX" -std=c++20 -O1 -g -Wall -Wextra -Werror -pedantic \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I"$ROOT/tools/lingshu-flexible-ps4" \
  "$ROOT/tools/lingshu-flexible-ps4/test_flexible_policy.cpp" \
  -o "$TMP/test-flexible"
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 "$TMP/test-flexible"
