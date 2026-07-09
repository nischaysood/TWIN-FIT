from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    FIREWORKS_API_KEY: str = ""
    FIREWORKS_BASE_URL: str = "https://api.fireworks.ai/inference/v1"
    GEMMA_MODEL: str = "accounts/fireworks/models/kimi-k2p6"
    FLUX_MODEL: str = "flux-kontext-pro"
    REDIS_URL: str = "redis://localhost:6379"
    MAX_IMAGE_SIZE_MB: int = 10

    class Config:
        env_file = ".env"

settings = Settings()
