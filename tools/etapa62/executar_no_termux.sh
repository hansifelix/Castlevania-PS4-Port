#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
command -v clang++ >/dev/null || { echo 'KAZUMA62: rode pkg install clang'; exit 1; }
# Somente testes de logica em Android. Cabecalho TESTE deliberadamente isolado.
mkdir -p "$HOME/kazuma62"
clang++ -std=c++17 -Wall -Wextra -Werror -O1 -Itests/include \
  ps4_vulkan_bridge.cpp tests/test_bridge.cpp -o "$HOME/kazuma62/ponte_teste"
"$HOME/kazuma62/ponte_teste"
echo 'KAZUMA62: TESTE_LOCAL=OK; cross-compilacao PS4 somente pelo GitHub Actions.'
