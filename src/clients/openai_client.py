from __future__ import annotations

import json
from typing import Any

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.keyvault.secrets import SecretClient
from openai import AzureOpenAI

from src.utils.logging_utils import get_logger, log_with_context

logger = get_logger(__name__)


class AzureOpenAIRiskClient:
    def __init__(
        self,
        endpoint: str,
        deployment: str,
        api_version: str,
        keyvault_uri: str | None = None,
        api_key_secret_name: str | None = None,
    ) -> None:
        self.deployment = deployment

        if keyvault_uri and api_key_secret_name:
            credential = DefaultAzureCredential()
            secret_client = SecretClient(vault_url=keyvault_uri, credential=credential)
            api_key = secret_client.get_secret(api_key_secret_name).value
            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
            )
            auth_mode = "keyvault-api-key"
        else:
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                credential,
                "https://cognitiveservices.azure.com/.default",
            )
            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                azure_ad_token_provider=token_provider,
                api_version=api_version,
            )
            auth_mode = "managed-identity"

        log_with_context(logger, "Azure OpenAI client initialized", deployment=deployment, auth_mode=auth_mode)

    def infer_risk(self, prompt: str, telemetry: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(telemetry, ensure_ascii=True)
        completion = self.client.responses.create(
            model=self.deployment,
            input=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        "Analiza la siguiente telemetria y retorna JSON con llaves: "
                        "summary, risk_score (0-1), severity, evidence (lista), recommendation, actionable_steps.\\n"
                        f"TELEMETRIA: {payload}"
                    ),
                },
            ],
            temperature=0.2,
        )

        raw = completion.output_text.strip()
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = {
                "summary": raw,
                "risk_score": 0.5,
                "severity": "medium",
                "evidence": ["Respuesta no-JSON del modelo"],
                "recommendation": "Revisar salida del modelo y reforzar prompt.",
                "actionable_steps": ["Habilitar salida JSON estricta"],
            }

        log_with_context(logger, "Risk inference completed", risk_score=result.get("risk_score"))
        return result
