from src.clients.openai_client import AzureOpenAIRiskClient


class FakeResponsesAPI:
    @staticmethod
    def create(**_kwargs):
        class Response:
            output_text = '{"summary":"ok","risk_score":0.8,"severity":"high","evidence":["e1"],"recommendation":"r1","actionable_steps":["s1"]}'

        return Response()


class FakeAzureOpenAI:
    def __init__(self, **_kwargs):
        self.responses = FakeResponsesAPI()


def test_openai_infer_risk_json(monkeypatch):
    monkeypatch.setattr("src.clients.openai_client.AzureOpenAI", FakeAzureOpenAI)
    monkeypatch.setattr("src.clients.openai_client.DefaultAzureCredential", lambda: object())
    monkeypatch.setattr("src.clients.openai_client.get_bearer_token_provider", lambda *_a, **_k: lambda: "token")

    client = AzureOpenAIRiskClient(
        endpoint="https://example.openai.azure.com",
        deployment="gpt-4o",
        api_version="2024-12-01-preview",
    )
    result = client.infer_risk("prompt", {"events": []})

    assert result["risk_score"] == 0.8
    assert result["severity"] == "high"
