from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    base_rpc_url: str | None = None
    ethereum_rpc_url: str | None = None
    solana_rpc_url: str | None = None
    trongrid_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
