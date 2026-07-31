from __future__ import annotations

from typing import Any

from azure.kusto.data import KustoClient, KustoConnectionStringBuilder

from src.utils.logging_utils import get_logger, log_with_context

logger = get_logger(__name__)


class ADXClient:
    def __init__(
        self,
        cluster_uri: str,
        database: str,
        managed_identity_client_id: str | None = None,
    ) -> None:
        self.database = database
        self.cluster_uri = cluster_uri

        kcsb = KustoConnectionStringBuilder.with_aad_managed_service_identity_authentication(
            cluster_uri,
            client_id=managed_identity_client_id,
        )
        auth_mode = "managed-identity"

        self.client = KustoClient(kcsb)
        log_with_context(logger, "ADX client initialized", cluster_uri=cluster_uri, auth_mode=auth_mode)

    def query(self, query_text: str, properties: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        response = self.client.execute(self.database, query_text, properties=properties)
        primary = response.primary_results[0]
        rows: list[dict[str, Any]] = []
        for row in primary:
            rows.append({col.column_name: row[col.column_name] for col in primary.columns})

        log_with_context(logger, "ADX query executed", row_count=len(rows))
        return rows
