from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings:
    """集中读取环境变量，避免业务代码散落配置细节。"""

    app_name: str = "ReSale Agent"
    api_prefix: str = "/api/v1"
    environment: str = os.getenv("RESALE_AGENT_ENV", "development")
    db_path: Path = Path(os.getenv("RESALE_AGENT_DB_PATH", PROJECT_ROOT / "data" / "resale.db"))
    upload_dir: Path = Path(os.getenv("RESALE_AGENT_UPLOAD_DIR", PROJECT_ROOT / "uploads"))
    max_images: int = int(os.getenv("RESALE_AGENT_MAX_IMAGES", "4"))
    max_image_bytes: int = int(os.getenv("RESALE_AGENT_MAX_IMAGE_BYTES", str(10 * 1024 * 1024)))
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_vision_model: str = os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini")
    openai_text_model: str = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")


def get_settings() -> Settings:
    # 每次创建 Settings 都重新读环境变量，方便测试替换数据库路径。
    return Settings()

