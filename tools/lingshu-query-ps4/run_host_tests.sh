#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CXX="${CXX:-c++}"
"$CXX" -std=c++20 -O1 -g -Wall -Wextra -Werror -pedantic \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I"$ROOT/tools/lingshu-query-ps4" \
  "$ROOT/tools/lingshu-query-ps4/test_virtual_query_policy.cpp" \
  -o "$TMP/query-test"
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 "$TMP/query-test"
