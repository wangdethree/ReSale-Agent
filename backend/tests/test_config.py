from __future__ import annotations

from pathlib import Path

from backend.app.core.config import get_settings


def test_settings_reads_project_env_file(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env"
    db_path = tmp_path / "from-env-file.db"
    env_file.write_text(
        f"RESALE_AGENT_DB_PATH={db_path}\nOPENAI_VISION_MODEL=vision-from-file\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("RESALE_AGENT_DB_PATH", raising=False)
    monkeypatch.delenv("OPENAI_VISION_MODEL", raising=False)
    monkeypatch.setenv("RESALE_AGENT_ENV_FILE", str(env_file))

    settings = get_settings()

    assert settings.db_path == Path(db_path)
    assert settings.openai_vision_model == "vision-from-file"


def test_real_environment_overrides_env_file(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_VISION_MODEL=vision-from-file\n", encoding="utf-8")

    monkeypatch.setenv("RESALE_AGENT_ENV_FILE", str(env_file))
    monkeypatch.setenv("OPENAI_VISION_MODEL", "vision-from-environment")

    settings = get_settings()

    assert settings.openai_vision_model == "vision-from-environment"

