#!/usr/bin/env bash
# Compile and exercise the SAME native diagnostic C++ on Linux with mocks.
# This does NOT emulate PS4 kernel behavior or prove that a game can start.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$ROOT/tools/lingshu-native-ps4"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CXX="${CXX:-c++}"
"$CXX" -std=c++20 -O1 -g -Wall -Wextra -Werror -pedantic \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I"$SRC/host_stubs" -I"$SRC" \
  "$SRC/native_api_console.cpp" \
  "$SRC/native_reserve_ps4_bridge.cpp" \
  "$SRC/host_stubs/mock_ps4_api.cpp" \
  -o "$TMP/diagnostico-linux-mock"
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 LINGSHU190_MOCK_MODE=success \
  "$TMP/diagnostico-linux-mock" > "$TMP/ok.txt"
grep -Fq 'LINGSHU188_SUMMARY attempts=18 exact=18 relocated=0 native_failed=0 unsafe=0 stopped=0' "$TMP/ok.txt"
grep -Fq 'LINGSHU190_DIAGNOSTIC=COMPLETED_CHECK_SUMMARY_NOT_GAME_SUCCESS' "$TMP/ok.txt"
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 LINGSHU190_MOCK_MODE=deny \
  "$TMP/diagnostico-linux-mock" > "$TMP/deny.txt"
grep -Fq 'LINGSHU188_SUMMARY attempts=6 exact=0 relocated=0 native_failed=6 unsafe=0 stopped=0' "$TMP/deny.txt"
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 LINGSHU190_MOCK_MODE=cleanup_fail \
  "$TMP/diagnostico-linux-mock" > "$TMP/cleanup.txt"
grep -Fq 'LINGSHU188_SUMMARY attempts=1 exact=0 relocated=0 native_failed=0 unsafe=1 stopped=1' "$TMP/cleanup.txt"
echo 'LINGSHU_PUBLIC_NATIVE_CPP_MOCK=PASS_HOST_ONLY_NOT_PS4'
