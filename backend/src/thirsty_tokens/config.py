from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

MAX_OUTPUT_TOKENS = 500  # hardcoded server-side; never taken from the request

DEFAULT_MODELS_PATH = Path(__file__).resolve().parents[2] / "models.yaml"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TT_")

    aws_region: str = "eu-north-1"  # org SCP only allows eu-north-1
    max_input_chars: int = 2000
    models_path: Path = DEFAULT_MODELS_PATH
