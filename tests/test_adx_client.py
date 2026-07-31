from types import SimpleNamespace

from src.clients.adx_client import ADXClient


class FakeTable:
    def __init__(self) -> None:
        self.columns = [SimpleNamespace(column_name="UserId"), SimpleNamespace(column_name="EventType")]
        self._rows = [
            {"UserId": "u1", "EventType": "failed_auth"},
            {"UserId": "u2", "EventType": "login"},
        ]

    def __iter__(self):
        return iter(self._rows)


class FakeResponse:
    def __init__(self) -> None:
        self.primary_results = [FakeTable()]


class FakeKustoClient:
    def __init__(self, *_args, **_kwargs):
        pass

    def execute(self, _db, _query, properties=None):
        return FakeResponse()


def test_adx_query_returns_rows(monkeypatch):
    monkeypatch.setattr("src.clients.adx_client.KustoClient", FakeKustoClient)
    monkeypatch.setattr(
        "src.clients.adx_client.KustoConnectionStringBuilder.with_aad_managed_service_identity_authentication",
        lambda _uri, **_kwargs: object(),
    )

    client = ADXClient(cluster_uri="https://cluster.kusto.windows.net", database="db")
    rows = client.query("Telemetry | take 2")

    assert len(rows) == 2
    assert rows[0]["UserId"] == "u1"
