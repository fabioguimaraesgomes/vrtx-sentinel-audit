from src.adapters.copilot_extension_adapter import CopilotExtensionAdapter


def test_copilot_adapter_output_shape():
    adapter = CopilotExtensionAdapter(test_mode=True)
    payload = adapter.to_copilot_security(
        {
            "id": "r-1",
            "severity": "high",
            "risk_score": 0.82,
            "summary": "Suspicious beaconing",
            "evidence": ["high-frequency outbound"],
            "recommendation": "Block destination",
            "actionable_steps": ["Contain host", "Collect memory image"],
        }
    )

    assert payload["metadata"]["mode"] == "test"
    assert payload["risk"]["severity"] == "high"
    assert payload["evidence"][0]["type"] == "indicator"
    assert len(payload["actionable_steps"]) == 2
