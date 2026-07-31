from __future__ import annotations

from typing import Any

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder

from src.utils.logging_utils import get_logger, log_with_context

logger = get_logger(__name__)


class ADXClient:
    def __init__(
        self,
        cluster_uri: str,
        database: str,
        managed_identity_client_id: str | None = None,
        keyvault_uri: str | None = None,
        app_id_secret_name: str | None = None,
        app_key_secret_name: str | None = None,
    ) -> None:
        self.database = database
        self.cluster_uri = cluster_uri

        if keyvault_uri and app_id_secret_name and app_key_secret_name:
            credential = DefaultAzureCredential(managed_identity_client_id=managed_identity_client_id)
            secret_client = SecretClient(vault_url=keyvault_uri, credential=credential)
            app_id = secret_client.get_secret(app_id_secret_name).value
            app_key = secret_client.get_secret(app_key_secret_name).value
            kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
                connection_string=cluster_uri,
                aad_app_id=app_id,
                app_key=app_key,
                authority_id="organizations",
            )
            auth_mode = "keyvault-app-key"
        else:
            kcsb = KustoConnectionStringBuilder.with_az_cli_authentication(cluster_uri)
            auth_mode = "managed-identity-or-cli"

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
