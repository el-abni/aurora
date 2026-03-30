#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SHARE="${AURORA_SHARE_DIR:-$HOME/.local/share/aurora}"
TARGET_BIN="${AURORA_BIN_DIR:-$HOME/.local/bin}"

fail() {
  printf "ERRO: %s\n" "$1" >&2
  exit 1
}

require_file() {
  local path="$1"
  [[ -e "$path" ]] || fail "faltou arquivo obrigatorio: $path"
}

command -v python3 >/dev/null 2>&1 || fail "python3 nao esta disponivel neste host"
command -v install >/dev/null 2>&1 || fail "o comando 'install' nao esta disponivel neste host"

require_file "$ROOT/VERSION"
require_file "$ROOT/bin/aurora"
require_file "$ROOT/bin/auro"
require_file "$ROOT/python/aurora/__main__.py"
require_file "$ROOT/resources/help.txt"

mkdir -p "$TARGET_SHARE" "$TARGET_BIN"
rm -rf "$TARGET_SHARE/python" "$TARGET_SHARE/resources"
mkdir -p "$TARGET_SHARE/python" "$TARGET_SHARE/resources"

cp -R "$ROOT/python/." "$TARGET_SHARE/python/"
cp -R "$ROOT/resources/." "$TARGET_SHARE/resources/"
install -m 0644 "$ROOT/VERSION" "$TARGET_SHARE/VERSION"
install -m 0755 "$ROOT/bin/aurora" "$TARGET_BIN/aurora"
install -m 0755 "$ROOT/bin/auro" "$TARGET_BIN/auro"

printf "Aurora %s instalada em %s\n" "$(cat "$ROOT/VERSION")" "$TARGET_SHARE"
printf "Launchers instalados em %s\n" "$TARGET_BIN"
if [[ ":$PATH:" != *":$TARGET_BIN:"* ]]; then
  printf "Nota: %s ainda nao esta no PATH desta shell.\n" "$TARGET_BIN"
fi
printf "Teste rapido: aurora --help\n"
