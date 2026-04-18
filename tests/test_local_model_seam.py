from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib import error as urllib_error

from aurora.install.planner import plan_text
from aurora.local_model.contracts import LocalModelProviderError, LocalModelRequest, LocalModelResponse
from aurora.observability.dev_command import render_dev_report
from aurora.observability.decision_record import decision_record_to_dict
from support import setup_host_package_testbed


class _ValidProvider:
    provider_name = "valid_fixture"

    def assist(self, request: LocalModelRequest) -> LocalModelResponse:
        if request.capability == "disambiguate_limited":
            text = "Escolha obs-studio ou obs_studio."
        else:
            text = "Resumo seguro do kernel deterministico."
        return LocalModelResponse(capability=request.capability, text=text)


class _ForbiddenCapabilityProvider:
    provider_name = "forbidden_fixture"

    def assist(self, _request: LocalModelRequest) -> LocalModelResponse:
        return LocalModelResponse(capability="route", text="Vou trocar a rota.")


class _MismatchedCapabilityProvider:
    provider_name = "mismatch_fixture"

    def assist(self, _request: LocalModelRequest) -> LocalModelResponse:
        return LocalModelResponse(capability="explain", text="Explicacao fora da capacidade pedida.")


class _EmptyOutputProvider:
    provider_name = "empty_fixture"

    def assist(self, request: LocalModelRequest) -> LocalModelResponse:
        return LocalModelResponse(capability=request.capability, text="   ")


class _RichOutputProvider:
    provider_name = "rich_fixture"

    def assist(self, request: LocalModelRequest) -> LocalModelResponse:
        return LocalModelResponse(
            capability=request.capability,
            text="nao polir facts.local_model.\nsegunda linha do provider.",
        )


class _FailingProvider:
    provider_name = "failing_fixture"

    def assist(self, _request: LocalModelRequest) -> LocalModelResponse:
        raise LocalModelProviderError("provider_connection_error", provider_name=self.provider_name)


class _TimeoutProvider:
    provider_name = "timeout_fixture"

    def assist(self, _request: LocalModelRequest) -> LocalModelResponse:
        raise LocalModelProviderError("provider_timeout", provider_name=self.provider_name)


class LocalModelSeamTests(unittest.TestCase):
    def test_model_on_without_provider_falls_back_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("firefox|Firefox",),
            )
            payload = decision_record_to_dict(plan_text("procurar firefox", environ=env), model_mode="model_on", environ=env)

            self.assertEqual(payload["facts"]["local_model"]["mode"], "model_on")
            self.assertEqual(payload["facts"]["local_model"]["status"], "fallback_deterministic")
            self.assertEqual(payload["facts"]["local_model"]["fallback_reason"], "provider_not_configured")
            self.assertEqual(payload["facts"]["execution_route"]["route_id"], "host_package.procurar")

    def test_provider_cannot_return_forbidden_capability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("firefox|Firefox",),
            )
            payload = decision_record_to_dict(
                plan_text("procurar firefox", environ=env),
                model_mode="model_on",
                model_provider=_ForbiddenCapabilityProvider(),
                environ=env,
            )

            self.assertEqual(payload["facts"]["local_model"]["status"], "fallback_deterministic")
            self.assertEqual(
                payload["facts"]["local_model"]["fallback_reason"],
                "provider_invalid_response",
            )
            self.assertEqual(payload["facts"]["policy"]["policy_outcome"], "allow")

    def test_model_on_keeps_kernel_identical_for_ambiguous_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("obs-studio|OBS Studio", "obs_studio|OBS Studio underscore"),
            )
            record = plan_text("instalar obs studio", environ=env)
            payload_off = decision_record_to_dict(record, model_mode="model_off", environ=env)
            payload_on = decision_record_to_dict(
                record,
                model_mode="model_on",
                model_provider=_ValidProvider(),
                environ=env,
            )

            self.assertEqual(payload_off["facts"]["outcome"], payload_on["facts"]["outcome"])
            self.assertEqual(
                payload_off["facts"]["target_resolution"],
                payload_on["facts"]["target_resolution"],
            )
            self.assertEqual(
                payload_on["facts"]["local_model"]["requested_capability"],
                "disambiguate_limited",
            )
            self.assertIn("obs-studio", payload_on["facts"]["local_model"]["output_text"])

    def test_provider_capability_mismatch_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("firefox|Firefox",),
            )
            payload = decision_record_to_dict(
                plan_text("procurar firefox", environ=env),
                model_mode="model_on",
                model_provider=_MismatchedCapabilityProvider(),
                environ=env,
            )

            self.assertEqual(payload["facts"]["local_model"]["status"], "fallback_deterministic")
            self.assertEqual(
                payload["facts"]["local_model"]["fallback_reason"],
                "provider_invalid_response",
            )

    def test_provider_empty_output_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("firefox|Firefox",),
            )
            payload = decision_record_to_dict(
                plan_text("procurar firefox", environ=env),
                model_mode="model_on",
                model_provider=_EmptyOutputProvider(),
                environ=env,
            )

            self.assertEqual(payload["facts"]["local_model"]["status"], "fallback_deterministic")
            self.assertEqual(
                payload["facts"]["local_model"]["fallback_reason"],
                "provider_returned_empty_output",
            )
            self.assertEqual(payload["facts"]["local_model"]["provider_name"], "empty_fixture")

    def test_configured_ollama_connection_error_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("firefox|Firefox",),
            )
            env["AURORA_LOCAL_MODEL_PROVIDER"] = "ollama"
            env["AURORA_LOCAL_MODEL_MODEL"] = "qwen2.5:3b-instruct"
            env["AURORA_LOCAL_MODEL_URL"] = "http://127.0.0.1:11434"
            env["AURORA_LOCAL_MODEL_TIMEOUT_MS"] = "50"

            with mock.patch(
                "aurora.local_model.provider_ollama.urllib_request.urlopen",
                side_effect=urllib_error.URLError(ConnectionRefusedError("refused")),
            ):
                payload = decision_record_to_dict(
                    plan_text("procurar firefox", environ=env),
                    model_mode="model_on",
                    environ=env,
                )

            self.assertEqual(payload["facts"]["local_model"]["mode"], "model_on")
            self.assertEqual(payload["facts"]["local_model"]["status"], "fallback_deterministic")
            self.assertEqual(payload["facts"]["local_model"]["provider_name"], "ollama")
            self.assertEqual(
                payload["facts"]["local_model"]["fallback_reason"],
                "provider_connection_error",
            )
            self.assertEqual(payload["facts"]["execution_route"]["route_id"], "host_package.procurar")

    def test_legacy_provider_not_configured_reason_is_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("firefox|Firefox",),
            )
            with mock.patch(
                "aurora.local_model.seam.resolve_local_model_provider_from_environment",
                return_value=(None, "Provider_not_configured"),
            ):
                payload = decision_record_to_dict(
                    plan_text("procurar firefox", environ=env),
                    model_mode="model_on",
                    environ=env,
                )

            self.assertEqual(payload["facts"]["local_model"]["status"], "fallback_deterministic")
            self.assertEqual(payload["facts"]["local_model"]["fallback_reason"], "provider_not_configured")

    def test_render_keeps_fallback_reason_in_canonical_snake_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("firefox|Firefox",),
            )
            with mock.patch(
                "aurora.local_model.seam.resolve_local_model_provider_from_environment",
                return_value=(None, "Provider_not_configured"),
            ):
                rendered = render_dev_report(
                    "procurar firefox",
                    model_mode="model_on",
                    environ=env,
                )

            self.assertIn("fallback_reason:         provider_not_configured", rendered)

    def test_render_disabled_local_model_block_keeps_only_minimal_audit_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("firefox|Firefox",),
            )
            payload = decision_record_to_dict(
                plan_text("procurar firefox", environ=env),
                model_mode="model_off",
                environ=env,
            )
            rendered = render_dev_report("procurar firefox", model_mode="model_off", environ=env)

            self.assertEqual(payload["facts"]["local_model"]["mode"], "model_off")
            self.assertEqual(payload["facts"]["local_model"]["status"], "disabled")
            self.assertEqual(payload["facts"]["local_model"]["provider_name"], "")
            self.assertEqual(payload["facts"]["local_model"]["fallback_reason"], "")
            self.assertEqual(payload["facts"]["local_model"]["output_text"], "")
            self.assertIn("Local model seam", rendered)
            self.assertIn("mode:                    model_off", rendered)
            self.assertIn("status:                  disabled", rendered)
            self.assertIn("requested_capability:    summarize", rendered)
            self.assertNotIn("provider_name:", rendered)
            self.assertNotIn("fallback_reason:", rendered)
            self.assertNotIn("output_text:", rendered)
            self.assertNotIn("authority_profile:", rendered)
            self.assertNotIn("allowed_capabilities:", rendered)
            self.assertNotIn("forbidden_authorities:", rendered)
            self.assertNotIn("consumed_sections:", rendered)
            self.assertNotIn("input_schema_id:", rendered)

    def test_render_completed_local_model_block_preserves_raw_output_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("firefox|Firefox",),
            )
            payload = decision_record_to_dict(
                plan_text("procurar firefox", environ=env),
                model_mode="model_on",
                model_provider=_RichOutputProvider(),
                environ=env,
            )
            rendered = render_dev_report(
                "procurar firefox",
                model_mode="model_on",
                model_provider=_RichOutputProvider(),
                environ=env,
            )

            self.assertEqual(payload["facts"]["local_model"]["status"], "completed")
            self.assertEqual(payload["facts"]["local_model"]["provider_name"], "rich_fixture")
            self.assertEqual(
                payload["facts"]["local_model"]["output_text"],
                "nao polir facts.local_model.\nsegunda linha do provider.",
            )
            self.assertIn("provider_name:           rich_fixture", rendered)
            self.assertIn("output_text:             nao polir facts.local_model.", rendered)
            self.assertIn("\n                         segunda linha do provider.", rendered)
            self.assertNotIn("Não polir facts.local_model.", rendered)
            self.assertNotIn("fallback_reason:", rendered)

    def test_render_fallback_local_model_block_keeps_relevant_facts_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="debian",
                distro_id="ubuntu",
                distro_like="debian",
                repo_packages=("firefox|Firefox",),
            )
            payload = decision_record_to_dict(
                plan_text("procurar firefox", environ=env),
                model_mode="model_on",
                model_provider=_FailingProvider(),
                environ=env,
            )
            rendered = render_dev_report(
                "procurar firefox",
                model_mode="model_on",
                model_provider=_FailingProvider(),
                environ=env,
            )

            self.assertEqual(payload["facts"]["local_model"]["status"], "fallback_deterministic")
            self.assertEqual(payload["facts"]["local_model"]["provider_name"], "failing_fixture")
            self.assertEqual(payload["facts"]["local_model"]["fallback_reason"], "provider_connection_error")
            self.assertEqual(payload["facts"]["local_model"]["output_text"], "")
            self.assertIn("provider_name:           failing_fixture", rendered)
            self.assertIn("fallback_reason:         provider_connection_error", rendered)
            self.assertNotIn("output_text:", rendered)

    def test_blocked_explain_preserves_kernel_under_provider_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, _state_file = setup_host_package_testbed(
                root,
                family="arch",
                distro_id="cachyos",
                distro_like="arch",
                repo_packages=("sudo|sudo",),
                installed_packages=("sudo",),
            )
            payload = decision_record_to_dict(
                plan_text("remover sudo", environ=env),
                model_mode="model_on",
                model_provider=_TimeoutProvider(),
                environ=env,
            )

            self.assertEqual(payload["facts"]["outcome"], "blocked")
            self.assertEqual(payload["facts"]["policy"]["policy_outcome"], "require_confirmation")
            self.assertEqual(payload["facts"]["local_model"]["requested_capability"], "explain")
            self.assertEqual(payload["facts"]["local_model"]["status"], "fallback_deterministic")
            self.assertEqual(payload["facts"]["local_model"]["provider_name"], "timeout_fixture")
            self.assertEqual(payload["facts"]["local_model"]["fallback_reason"], "provider_timeout")
            self.assertEqual(payload["stable_ids"]["route_id"], "host_package.remover")
            self.assertEqual(payload["facts"]["execution_route"]["route_id"], "host_package.remover")


if __name__ == "__main__":
    unittest.main()
