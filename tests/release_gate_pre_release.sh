#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT"

git diff --check
bash "$ROOT/tests/release_gate_pre_push.sh"
bash "$ROOT/tests/release_gate_v0_6_2.sh"
PYTHONPATH=python:tests python3 -m unittest discover -s tests -p 'test_bootstrap_smoke.py'
PYTHONPATH=python:tests python3 -m unittest discover -s tests -p 'test_installer_release.py'

printf "release_gate_pre_release: ok (gate automatizado; tests/REVIEW_CHECKLIST.md e terminal real continuam obrigatorios)\n"
