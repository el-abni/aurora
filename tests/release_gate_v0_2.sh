#!/usr/bin/env bash
set -euo pipefail

python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/audit_public_release.py

printf "release_gate_v0_2: ok\n"
