from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM defaults
    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-flash"

    # Per-agent overrides (optional)
    diagnostic_agent_provider: str | None = None
    diagnostic_agent_model: str | None = None
    rgm_agent_provider: str | None = None
    rgm_agent_model: str | None = None
    budget_agent_provider: str | None = None
    budget_agent_model: str | None = None

    # API keys
    google_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # LangFuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # App
    data_path: str = "data/dataset.csv"
    interventions_path: str = "data/interventions.csv"
    budget_weekly_allocation_mxn: float = 10000.0
    health_threshold: float = 60.0
    cors_origins: list[str] = ["http://localhost:3000"]
