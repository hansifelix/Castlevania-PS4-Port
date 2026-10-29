#!/usr/bin/env bash
# Linux-only checks of the actual generic VM adapter source.
# Does NOT allocate the guest's 4/6/64 GiB windows or execute PS4 code.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CXX="${CXX:-c++}"
SRC="$ROOT/tools/etapa146/platform_ps4_virtual_memory.cpp"
INC="$ROOT/tools/etapa185/host_stubs"
FLAGS=(-std=c++20 -O1 -g -Wall -Wextra -Werror -pedantic
       -fno-omit-frame-pointer -I"$INC")
"$CXX" "${FLAGS[@]}" -fsanitize=undefined \
  "$ROOT/tools/etapa185/test_page_commit_ledger.cpp" -o "$TMP/ledger"
"$TMP/ledger"
"$CXX" "${FLAGS[@]}" -fsanitize=undefined \
  "$SRC" "$ROOT/tools/etapa185/test_host_memory_adapter.cpp" -o "$TMP/host"
"$TMP/host"
"$CXX" "${FLAGS[@]}" -fsanitize=address,undefined \
  "$SRC" "$ROOT/tools/etapa202/test_quarantine_host.cpp" \
  -Wl,--wrap=mmap -Wl,--wrap=munmap -Wl,--wrap=mprotect -Wl,--wrap=madvise \
  -o "$TMP/quarantine"
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 "$TMP/quarantine"
"$CXX" "${FLAGS[@]}" -fsanitize=address,undefined \
  "$SRC" "$ROOT/tools/etapa203/test_ps4_page_16k_host.cpp" \
  -Wl,--wrap=sysconf -Wl,--wrap=mmap -o "$TMP/ps4page"
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 "$TMP/ps4page"
"$CXX" "${FLAGS[@]}" -fsanitize=address,undefined \
  "$SRC" "$ROOT/tools/etapa204/test_decommit_failure_host.cpp" \
  -Wl,--wrap=mmap -Wl,--wrap=mprotect -Wl,--wrap=madvise \
  -o "$TMP/decommit"
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 "$TMP/decommit"
echo 'LINGSHU_PUBLIC_REAL_VM_ADAPTER=PASS_LINUX_ONLY_NOT_PS4'
