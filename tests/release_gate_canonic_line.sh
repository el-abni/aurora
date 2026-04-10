#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT"

PYTHONPATH=python:tests python3 -m unittest discover -s tests -p 'test_*.py'
PYTHONPATH=python:tests python3 tests/audit_public_release.py
PYTHONPATH=python:tests python3 tests/audit_canonic_line.py
PYTHONPATH=python:tests python3 tests/audit_decision_record_contract.py
PYTHONPATH=python:tests python3 tests/audit_workflow_release.py

printf "release_gate_canonic_line: ok\n"
