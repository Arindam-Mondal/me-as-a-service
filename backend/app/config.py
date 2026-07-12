"""Application configuration loaded from environment / backend/.env.

All secrets and tunables live here so nothing is hardcoded (TECHNICAL_SPEC.md §10).
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env (config.py is at backend/app/config.py -> parents[1] == backend/)
_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # AI providers
    anthropic_api_key: str
    voyage_api_key: str

    # Supabase (service-role key is backend-only)
    supabase_url: str
    supabase_service_role_key: str

    # Models
    chat_model: str = "claude-haiku-4-5"
    embedding_model: str = "voyage-3"

    # Retrieval tuning
    retrieval_top_n: int = 20  # candidates per leg
    retrieval_top_k: int = 5   # final fused chunks
    rrf_k: int = 60            # RRF constant

    # Rate limiting — all env-tunable so limits can be changed without a redeploy.
    # Both caps reset at UTC midnight. The global cap is the hard ceiling on spend.
    rate_limit_enabled: bool = True
    session_question_limit: int = 10   # per session (sid cookie) per UTC day
    daily_question_limit: int = 100    # global per UTC day

    # HTTP / CORS — comma-separated allowed frontend origins (cookies need explicit
    # origins + allow_credentials, so "*" won't work).
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    # Optional regex to allow dynamic origins (e.g. Vercel preview deploys):
    # ALLOWED_ORIGIN_REGEX="https://.*\\.vercel\\.app". Empty = disabled.
    allowed_origin_regex: str = ""

    # Session cookie flags — cross-site (Vercel <-> Render) needs SameSite=None; Secure.
    # Local dev defaults to lax/insecure.
    cookie_samesite: str = "lax"  # "lax" | "none" | "strict"
    cookie_secure: bool = False

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()  # type: ignore[call-arg]
