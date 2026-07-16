from __future__ import annotations

import json
from typing import Any

import requests

from backend.app.core.config import get_settings


class TextModelService:
    """OpenAI 兼容文本模型 JSON 调用助手。"""

    def generate_json(self, system_prompt: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        settings = get_settings()
        if not settings.openai_api_key:
            return None

        response = requests.post(
            f"{settings.openai_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openai_text_model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(payload, ensure_ascii=False),
                    },
                ],
            },
            timeout=60,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = self._parse_json(content)
        if not isinstance(parsed, dict):
            raise ValueError("文本模型返回内容不是 JSON 对象")
        return parsed

    def _parse_json(self, content: str | dict[str, Any]) -> Any:
        if isinstance(content, dict):
            return content
        text = content.strip()
        if text.startswith("```"):
            lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
            text = "\n".join(lines).strip()
        return json.loads(text)

