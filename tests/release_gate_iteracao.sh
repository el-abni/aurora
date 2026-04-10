#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT"

git diff --check
PYTHONPATH=python:tests python3 tests/audit_decision_record_contract.py
PYTHONPATH=python:tests python3 -m unittest discover -s tests -p 'test_bootstrap_smoke.py'
PYTHONPATH=python:tests python3 -m unittest discover -s tests -p 'test_installer_release.py'
PYTHONPATH=python:tests python3 -m unittest discover -s tests -p 'test_decision_record.py'

printf "release_gate_iteracao: ok\n"
