#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT"

mapfile -t PUBLIC_TESTS < <(git ls-files 'tests/test_*.py')
PYTHONPATH=python:tests python3 -m unittest "${PUBLIC_TESTS[@]}"
PYTHONPATH=python:tests python3 tests/audit_public_release.py
PYTHONPATH=python:tests python3 tests/audit_canonic_line.py
PYTHONPATH=python:tests python3 tests/audit_decision_record_contract.py
PYTHONPATH=python:tests python3 tests/audit_factual_hotspots.py
PYTHONPATH=python:tests python3 tests/audit_factual_baseline.py
PYTHONPATH=python:tests python3 tests/audit_observability_canonical_facts.py
PYTHONPATH=python:tests python3 tests/audit_local_model_eval_baseline.py
PYTHONPATH=python:tests python3 tests/audit_workflow_release.py

printf "release_gate_canonic_line: ok\n"
