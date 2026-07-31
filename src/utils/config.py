import os
from dataclasses import dataclass


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    adx_cluster_uri: str
    adx_database: str
    adx_managed_identity_client_id: str | None
    keyvault_uri: str | None
    keyvault_adx_app_id_secret_name: str | None
    keyvault_adx_app_key_secret_name: str | None
    eventgrid_topic_endpoint: str
    eventgrid_topic_key_secret_name: str | None
    openai_endpoint: str
    openai_deployment: str
    openai_api_version: str
    openai_key_secret_name: str | None
    jwt_audience: str
    jwt_issuer: str
    jwt_hs256_secret: str | None
    cors_allowed_origins: list[str]
    security_csp: str
    rate_limit_per_minute: int
    idempotency_ttl_seconds: int


def load_settings() -> Settings:
    return Settings(
        adx_cluster_uri=os.getenv("ADX_CLUSTER_URI", "https://example.kusto.windows.net"),
        adx_database=os.getenv("ADX_DATABASE", "vrtxsentinel"),
        adx_managed_identity_client_id=os.getenv("ADX_MANAGED_IDENTITY_CLIENT_ID"),
        keyvault_uri=os.getenv("KEYVAULT_URI"),
        keyvault_adx_app_id_secret_name=os.getenv("KEYVAULT_ADX_APP_ID_SECRET_NAME"),
        keyvault_adx_app_key_secret_name=os.getenv("KEYVAULT_ADX_APP_KEY_SECRET_NAME"),
        eventgrid_topic_endpoint=os.getenv("EVENTGRID_TOPIC_ENDPOINT", "https://example.westus2-1.eventgrid.azure.net/api/events"),
        eventgrid_topic_key_secret_name=os.getenv("KEYVAULT_EVENTGRID_TOPIC_KEY_SECRET_NAME"),
        openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com"),
        openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        openai_key_secret_name=os.getenv("KEYVAULT_OPENAI_KEY_SECRET_NAME"),
        jwt_audience=os.getenv("JWT_AUDIENCE", "vrtx-sentinel-api"),
        jwt_issuer=os.getenv("JWT_ISSUER", "https://login.microsoftonline.com/common/v2.0"),
        jwt_hs256_secret=os.getenv("JWT_HS256_SECRET"),
        cors_allowed_origins=_split_csv(os.getenv("CORS_ALLOWED_ORIGINS")),
        security_csp=os.getenv(
            "SECURITY_CSP",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none';",
        ),
        rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "120")),
        idempotency_ttl_seconds=int(os.getenv("IDEMPOTENCY_TTL_SECONDS", "600")),
    )
