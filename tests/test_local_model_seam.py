from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aurora.install.planner import plan_text
from aurora.local_model.contracts import LocalModelRequest, LocalModelResponse
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
                "provider_returned_forbidden_capability",
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
                "provider_returned_capability_mismatch",
            )


if __name__ == "__main__":
    unittest.main()
