#!/usr/bin/env bash
set -euo pipefail

TARGET_SHARE="${AURORA_SHARE_DIR:-$HOME/.local/share/aurora}"
TARGET_BIN="${AURORA_BIN_DIR:-$HOME/.local/bin}"

removed_any=0

if [[ -e "$TARGET_BIN/aurora" || -L "$TARGET_BIN/aurora" ]]; then
  rm -f "$TARGET_BIN/aurora"
  removed_any=1
fi

if [[ -e "$TARGET_BIN/auro" || -L "$TARGET_BIN/auro" ]]; then
  rm -f "$TARGET_BIN/auro"
  removed_any=1
fi

if [[ -d "$TARGET_SHARE" ]]; then
  rm -rf "$TARGET_SHARE"
  removed_any=1
fi

if [[ "$removed_any" -eq 1 ]]; then
  printf "Aurora removida de %s e %s\n" "$TARGET_SHARE" "$TARGET_BIN"
else
  printf "Nada para remover em %s e %s\n" "$TARGET_SHARE" "$TARGET_BIN"
fi
