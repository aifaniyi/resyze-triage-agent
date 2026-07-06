from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 8090

    # Grafana MCP
    grafana_mcp_url: str = "http://grafana-mcp-server.resyze.svc.cluster.local:8080/sse"

    # LLM
    llm_provider: str = "google"  # "google" or "openai"
    llm_model: str = "gemini-2.0-flash"
    llm_api_key: str = ""

    # NATS (for sending triage results to mailer)
    nats_url: str = "nats://localhost:4222"
    nats_mailer_subject: str = "email.events"
    alert_recipient_email: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
