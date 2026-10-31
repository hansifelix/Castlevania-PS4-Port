#!/usr/bin/env bash
set -euo pipefail
headers="${1:?pass pinned upstream runtime/src directory}"
root="$(cd "$(dirname "$0")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
g++ -std=c++20 -O2 -Wall -Wextra -Werror -pthread \
  -I"$headers" \
  "$root/tools/etapa144/platform_ps4_posix_core.cpp" \
  "$root/tools/etapa181/test_boot_stage.cpp" \
  -o "$tmp/boot-stage"
KAZUMA_DATA_ROOT="$tmp/boot" "$tmp/boot-stage" > "$tmp/result.txt" 2> "$tmp/stderr.txt"
grep -F 'LINGSHU181_REAL_BOOT_STAGE_LOG=PASSED_3_BRANCHES_9_PERSISTENT_MARKERS_NO_GAME' "$tmp/result.txt"
