#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT"

bash "$ROOT/tests/release_gate_canonic_line.sh"

printf "release_gate_v0_6_2: ok (gate historico da release v0.6.2; a regua corrente da linha e tests/release_gate_canonic_line.sh)\n"
