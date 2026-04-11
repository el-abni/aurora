#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "factual_hotspots_v0_7_0_cut3.json"
SCHEMA_PATH = ROOT / "python" / "aurora" / "contracts" / "decision_record_schema.py"
RENDER_PATH = ROOT / "python" / "aurora" / "observability" / "render.py"
def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def ok(message: str) -> None:
    print(f"OK: {message}")


def ensure(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def ast_signal_prefixes(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    prefixes: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name):
            continue
        if node.func.id not in {"_signal_value", "_has_any_signal"}:
            continue
        args = node.args[1:]
        for arg in args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.endswith(":"):
                prefixes.add(arg.value[:-1])
    return prefixes


def serializer_signal_prefixes() -> list[str]:
    return sorted(ast_signal_prefixes(SCHEMA_PATH))


def renderer_signal_prefixes() -> list[str]:
    return sorted(ast_signal_prefixes(RENDER_PATH))


def reparsing_modules() -> list[str]:
    modules: list[str] = []
    for path in sorted((ROOT / "python" / "aurora").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "trust_signals" not in text:
            continue
        if "_signal_value(" not in text and "_has_any_signal(" not in text:
            continue
        modules.append(relative(path))
    return modules


def main() -> int:
    fixture = read_json(FIXTURE_PATH)

    expected_modules = fixture["reparsing_modules"]
    expected_serializer = fixture["serializer_signal_prefixes"]
    expected_renderer = fixture["renderer_signal_prefixes"]

    actual_modules = reparsing_modules()
    actual_serializer = serializer_signal_prefixes()
    actual_renderer = renderer_signal_prefixes()

    ensure(actual_modules == expected_modules, "modulos que reparseiam trust_signals divergem do fixture factual")
    ensure(
        actual_serializer == expected_serializer,
        "prefixos trust_signals->facts em decision_record_schema.py divergem do fixture factual",
    )
    ensure(
        actual_renderer == expected_renderer,
        "prefixos trust_signals->render em render.py divergem do fixture factual",
    )
    ensure(fixture.get("critical_fact_paths"), "fixture factual precisa listar caminhos criticos")

    ok("mapa factual de hotspots alinhado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
