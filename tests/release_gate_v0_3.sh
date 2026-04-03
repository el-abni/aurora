#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=python python3 -m unittest discover -s tests -p 'test_*.py'
PYTHONPATH=python python3 tests/audit_public_release.py

printf "release_gate_v0_3: ok\n"
