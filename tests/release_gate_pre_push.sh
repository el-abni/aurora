#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT"

git diff --check
bash "$ROOT/tests/release_gate_canonic_line.sh"

printf "release_gate_pre_push: ok\n"
