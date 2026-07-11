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

    class Config:
        env_file = ".env"

settings = Settings()
