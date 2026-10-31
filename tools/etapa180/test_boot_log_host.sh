#!/usr/bin/env bash
# Host side: real logger source + pinned original platform.h (passed by CI).
set -euo pipefail
headers="${1:?pass pinned upstream runtime/src directory}"
root="$(cd "$(dirname "$0")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
g++ -std=c++20 -O2 -Wall -Wextra -Werror -pthread \
  -I"$headers" \
  "$root/tools/etapa144/platform_ps4_posix_core.cpp" \
  "$root/tools/etapa180/test_ps4_boot_log.cpp" \
  -o "$tmp/boot-log-test"
KAZUMA_DATA_ROOT="$tmp/boot" "$tmp/boot-log-test" > "$tmp/result.txt" 2> "$tmp/boot-stderr.txt"
grep -F 'LINGSHU180_REAL_PERSISTENT_BOOT_LOG=PASSED_ROTATION_402_LINES_4_THREADS_NO_GAME' "$tmp/result.txt"
KAZUMA_DATA_ROOT="/dev/null/not-a-directory" "$tmp/boot-log-test" fallback > "$tmp/fallback.txt" 2> "$tmp/fallback-stderr.txt"
grep -F 'LINGSHU180_STDERR_FALLBACK=PASSED_NO_GAME' "$tmp/fallback.txt"
grep -F 'LINGSHU180_ROOT_INACCESSIBLE_FALLBACK' "$tmp/fallback-stderr.txt"
