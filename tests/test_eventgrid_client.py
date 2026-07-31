from src.clients.eventgrid_client import VrtxEventGridPublisher


class FakePublisherClient:
    def __init__(self, *_args, **_kwargs):
        self.sent = []

    def send(self, events):
        self.sent.extend(events)


def test_publish_event_schema(monkeypatch):
    monkeypatch.setattr("src.clients.eventgrid_client.EventGridPublisherClient", FakePublisherClient)
    monkeypatch.setattr("src.clients.eventgrid_client.DefaultAzureCredential", lambda: object())

    publisher = VrtxEventGridPublisher("https://example.topic")
    payload = publisher.publish_risk_event(
        {
            "severity": "critical",
            "risk_score": 0.95,
            "summary": "High risk",
            "evidence": ["pattern-x"],
            "recommendation": "Isolate endpoint",
        }
    )

    assert payload["severity"] == "critical"
    assert payload["risk_score"] == 0.95
    assert "id" in payload
    assert "timestamp" in payload
