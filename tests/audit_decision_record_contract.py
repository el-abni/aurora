#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path

from aurora.contracts.decision_record_schema import DECISION_RECORD_SCHEMA_ID, validate_decision_record_payload
from aurora.install.execution_handoff import perform_execution
from aurora.install.planner import plan_text
from aurora.observability.decision_record import decision_record_to_dict
from aurora.observability.dev_command import render_dev_report
from support import setup_host_package_testbed


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def ok(message: str) -> None:
    print(f"OK: {message}")


def ensure(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def assert_planned_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        env, _state_file = setup_host_package_testbed(
            root,
            family="debian",
            distro_id="ubuntu",
            distro_like="debian",
            repo_packages=("firefox",),
        )
        payload = decision_record_to_dict(plan_text("procurar firefox", environ=env))
        ensure(not validate_decision_record_payload(payload), "payload planejado precisa validar no schema atual")
        ensure(payload["schema"]["schema_id"] == DECISION_RECORD_SCHEMA_ID, "schema_id precisa ser canonico")
        ensure(payload["stable_ids"]["action_id"] == "procurar", "action_id precisa ser minimo e estavel")
        ensure(payload["stable_ids"]["route_id"] == "host_package.procurar", "route_id precisa canonicalizar host_package.procurar")
        ensure(payload["stable_ids"]["event_id"] == "decision.planned", "event_id planejado precisa ser estavel")
        ensure("summary" not in payload["facts"], "facts nao pode carregar summary")
        ensure(payload["facts"]["execution_route"]["route_id"] == "host_package.procurar", "facts.execution_route precisa carregar route_id canonico")
        ensure(payload["facts"]["execution_route"]["legacy_route_name"] == "host_package.search", "route_name legado precisa continuar visivel")
        ensure(payload["execution_route"]["route_name"] == "host_package.search", "espelho legado precisa preservar route_name antigo")
        ensure(payload["presentation"]["summary"] == payload["summary"], "summary publico precisa viver em presentation e no espelho legado")
        ok("payload planejado alinhado")


def assert_executed_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        env, _state_file = setup_host_package_testbed(
            root,
            family="debian",
            distro_id="ubuntu",
            distro_like="debian",
            repo_packages=("firefox",),
        )
        _exit_code, executed_record, _message = perform_execution(
            plan_text("instalar firefox", environ=env),
            environ=env,
        )
        payload = decision_record_to_dict(executed_record)
        ensure(not validate_decision_record_payload(payload), "payload executado precisa validar no schema atual")
        ensure(payload["stable_ids"]["action_id"] == "instalar", "action_id executado precisa ser estavel")
        ensure(payload["stable_ids"]["event_id"] == "execution.executed", "event_id executado precisa ser estavel")
        ensure("summary" not in payload["facts"]["execution"], "facts.execution nao pode carregar summary")
        ensure("summary" not in payload["facts"]["execution"]["pre_probe"], "facts.pre_probe nao pode carregar summary")
        ensure("summary" not in payload["facts"]["execution"]["post_probe"], "facts.post_probe nao pode carregar summary")
        ensure(payload["presentation"]["execution"]["summary"], "presentation.execution precisa carregar a voz publica")
        ensure(payload["presentation"]["execution"]["pre_probe_summary"], "presentation.execution precisa carregar pre_probe_summary")
        ensure(payload["presentation"]["execution"]["post_probe_summary"], "presentation.execution precisa carregar post_probe_summary")
        ok("payload executado alinhado")


def assert_render_output() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        env, _state_file = setup_host_package_testbed(
            root,
            family="debian",
            distro_id="ubuntu",
            distro_like="debian",
            repo_packages=("firefox",),
        )
        rendered = render_dev_report("procurar firefox", environ=env)
        ensure("schema_version:" in rendered, "renderer precisa expor schema_version")
        ensure("action_id:" in rendered, "renderer precisa expor action_id")
        ensure("route_id:" in rendered, "renderer precisa expor route_id")
        ensure("event_id:" in rendered, "renderer precisa expor event_id")
        ok("render alinhado")


def main() -> int:
    assert_planned_contract()
    assert_executed_contract()
    assert_render_output()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
