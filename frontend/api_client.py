from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
env_file = Path(os.getenv("RESALE_AGENT_ENV_FILE", PROJECT_ROOT / ".env"))
if env_file.exists():
    load_dotenv(env_file, override=False)

API_BASE_URL = os.getenv("RESALE_AGENT_API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/")


class ApiClient:
    def _raise_for_status(self, response: requests.Response) -> None:
        if response.ok:
            return
        try:
            message = response.json().get("error", {}).get("message", response.text)
        except Exception:
            message = response.text
        raise RuntimeError(message)

    def create_session(self, category: str) -> dict[str, Any]:
        response = requests.post(f"{API_BASE_URL}/sessions", json={"category": category}, timeout=15)
        self._raise_for_status(response)
        return response.json()

    def analyze_images(self, session_id: str, files: list[Any]) -> dict[str, Any]:
        multipart = [
            ("files", (file.name, file.getvalue(), file.type or "image/jpeg"))
            for file in files
        ]
        response = requests.post(
            f"{API_BASE_URL}/sessions/{session_id}/images/analyze",
            files=multipart,
            timeout=60,
        )
        self._raise_for_status(response)
        return response.json()

    def confirm_product(self, session_id: str, product: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            f"{API_BASE_URL}/sessions/{session_id}/confirm",
            json={"product": product},
            timeout=20,
        )
        self._raise_for_status(response)
        return response.json()

    def next_question(self, session_id: str) -> dict[str, Any]:
        response = requests.get(f"{API_BASE_URL}/sessions/{session_id}/questions/next", timeout=15)
        self._raise_for_status(response)
        return response.json()

    def answer_question(self, session_id: str, field: str, answer: Any) -> dict[str, Any]:
        response = requests.post(
            f"{API_BASE_URL}/sessions/{session_id}/answers",
            json={"field": field, "answer": answer},
            timeout=15,
        )
        self._raise_for_status(response)
        return response.json()

    def generate_listing(self, session_id: str) -> dict[str, Any]:
        response = requests.post(f"{API_BASE_URL}/sessions/{session_id}/listing/generate", timeout=30)
        self._raise_for_status(response)
        return response.json()

    def negotiation_reply(self, session_id: str, buyer_message: str, floor_price: float | None) -> dict[str, Any]:
        payload = {"buyer_message": buyer_message, "user_floor_price": floor_price}
        response = requests.post(
            f"{API_BASE_URL}/sessions/{session_id}/negotiation/reply",
            json=payload,
            timeout=20,
        )
        self._raise_for_status(response)
        return response.json()

    def export_markdown(self, session_id: str) -> str:
        response = requests.get(f"{API_BASE_URL}/sessions/{session_id}/export", timeout=20)
        self._raise_for_status(response)
        return response.text
