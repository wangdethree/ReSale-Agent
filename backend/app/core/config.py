from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_project_env() -> None:
    env_file = Path(os.getenv("RESALE_AGENT_ENV_FILE", PROJECT_ROOT / ".env"))
    if env_file.exists():
        # 不覆盖真实环境变量，方便部署平台或命令行临时配置优先生效。
        load_dotenv(env_file, override=False)


class Settings:
    """集中读取环境变量，避免业务代码散落配置细节。"""

    def __init__(self) -> None:
        load_project_env()
        self.app_name: str = "ReSale Agent"
        self.api_prefix: str = "/api/v1"
        self.environment: str = os.getenv("RESALE_AGENT_ENV", "development")
        self.db_path: Path = Path(os.getenv("RESALE_AGENT_DB_PATH", PROJECT_ROOT / "data" / "resale.db"))
        self.upload_dir: Path = Path(os.getenv("RESALE_AGENT_UPLOAD_DIR", PROJECT_ROOT / "uploads"))
        self.max_images: int = int(os.getenv("RESALE_AGENT_MAX_IMAGES", "4"))
        self.max_image_bytes: int = int(os.getenv("RESALE_AGENT_MAX_IMAGE_BYTES", str(10 * 1024 * 1024)))
        self.openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
        self.openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.openai_vision_model: str = os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini")
        self.openai_text_model: str = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")


def get_settings() -> Settings:
    # 每次创建 Settings 都重新读环境变量，方便测试替换数据库路径。
    return Settings()
