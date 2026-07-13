from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    FIREWORKS_API_KEY: str = ""
    FIREWORKS_BASE_URL: str = "https://api.fireworks.ai/inference/v1"
    GEMMA_MODEL: str = "accounts/fireworks/models/kimi-k2p6"
    # OpenAI-compatible base URL for garment analysis. Empty = Fireworks.
    # Point at your AMD box (http://<AMD_IP>:8001/v1) to run REAL Gemma 3
    # on the MI300X — see gpu-server/serve_gemma.sh
    GEMMA_BASE_URL: str = ""
    GEMMA_API_KEY: str = ""
    # Gemini image-editing model for try-on (empty = engine disabled)
    GEMINI_IMAGE_MODEL: str = "models/gemini-3.1-flash-image"
    FLUX_MODEL: str = "flux-kontext-pro"
    # IDM-VTON bridge on AMD MI300X (see gpu-server/). Empty = not used.
    IDM_VTON_URL: str = ""
    # Public IDM-VTON demo on HuggingFace — real try-on without a GPU.
    # Set empty to disable. HF_TOKEN (free account) raises the GPU quota.
    TRYON_HF_SPACE: str = "yisol/IDM-VTON"
    HF_TOKEN: str = ""
    # Optional badge override, e.g. "IDM-VTON @ Modal (serverless GPU)"
    TRYON_ENGINE_LABEL: str = ""
    REDIS_URL: str = "redis://localhost:6379"
    MAX_IMAGE_SIZE_MB: int = 10

    # ── SaaS layer (all optional — empty = local demo mode) ──────────
    DATABASE_URL: str = ""            # Neon Postgres connection string
    REQUIRE_API_KEY: bool = False     # true on hosted deployments
    DEMO_API_KEY: str = "twinfit-demo"
    # Cloudflare R2 (S3-compatible) for try-on result images
    R2_ENDPOINT: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = ""
    R2_PUBLIC_BASE_URL: str = ""      # e.g. https://cdn.twinfit.app

    class Config:
        env_file = ".env"

settings = Settings()
