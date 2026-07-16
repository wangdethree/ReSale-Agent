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

    def list_sessions(self) -> list[dict[str, Any]]:
        response = requests.get(f"{API_BASE_URL}/sessions", timeout=15)
        self._raise_for_status(response)
        return response.json()

    def outcome_summary(self, category: str | None = None, sold_channel: str | None = None) -> dict[str, Any]:
        params = {
            key: value
            for key, value in {"category": category, "sold_channel": sold_channel}.items()
            if value
        }
        response = requests.get(
            f"{API_BASE_URL}/sessions/outcomes/summary",
            params=params,
            timeout=15,
        )
        self._raise_for_status(response)
        return response.json()

    def inventory_summary(self, category: str | None = None, inventory_status: str | None = None) -> dict[str, Any]:
        params = {
            key: value
            for key, value in {"category": category, "inventory_status": inventory_status}.items()
            if value
        }
        response = requests.get(
            f"{API_BASE_URL}/sessions/inventory/summary",
            params=params,
            timeout=15,
        )
        self._raise_for_status(response)
        return response.json()

    def get_session(self, session_id: str) -> dict[str, Any]:
        response = requests.get(f"{API_BASE_URL}/sessions/{session_id}", timeout=15)
        self._raise_for_status(response)
        return response.json()

    def delete_session(self, session_id: str) -> None:
        response = requests.delete(f"{API_BASE_URL}/sessions/{session_id}", timeout=15)
        self._raise_for_status(response)

    def record_sale_outcome(
        self,
        session_id: str,
        final_sold_price: float,
        sold_channel: str,
        sale_notes: str,
    ) -> dict[str, Any]:
        payload = {
            "final_sold_price": final_sold_price,
            "sold_channel": sold_channel,
            "sale_notes": sale_notes,
        }
        response = requests.post(f"{API_BASE_URL}/sessions/{session_id}/outcome", json=payload, timeout=15)
        self._raise_for_status(response)
        return response.json()

    def update_inventory(
        self,
        session_id: str,
        inventory_status: str,
        storage_location: str,
        inventory_notes: str,
    ) -> dict[str, Any]:
        payload = {
            "inventory_status": inventory_status,
            "storage_location": storage_location,
            "inventory_notes": inventory_notes,
        }
        response = requests.post(f"{API_BASE_URL}/sessions/{session_id}/inventory", json=payload, timeout=15)
        self._raise_for_status(response)
        return response.json()

    def record_listing_performance(self, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(f"{API_BASE_URL}/sessions/{session_id}/performance", json=payload, timeout=15)
        self._raise_for_status(response)
        return response.json()

    def import_market_data_csv(self, file: Any, source_name: str) -> dict[str, Any]:
        response = requests.post(
            f"{API_BASE_URL}/market-data/import",
            data={"source_name": source_name},
            files={"file": (file.name, file.getvalue(), "text/csv")},
            timeout=30,
        )
        self._raise_for_status(response)
        return response.json()

    def market_data_samples(
        self,
        category: str | None = None,
        source_type: str | None = None,
        active: bool | None = None,
    ) -> dict[str, Any]:
        params = {
            key: value
            for key, value in {"category": category, "source_type": source_type, "active": active}.items()
            if value is not None and value != ""
        }
        response = requests.get(f"{API_BASE_URL}/market-data/samples", params=params, timeout=15)
        self._raise_for_status(response)
        return response.json()

    def update_market_data_sample(self, item_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.patch(f"{API_BASE_URL}/market-data/samples/{item_id}", json=payload, timeout=15)
        self._raise_for_status(response)
        return response.json()

    def market_data_audit(self, limit: int = 10) -> dict[str, Any]:
        response = requests.get(f"{API_BASE_URL}/market-data/audit", params={"limit": limit}, timeout=15)
        self._raise_for_status(response)
        return response.json()

    def export_market_data_audit(self, export_format: str = "csv") -> str:
        response = requests.get(
            f"{API_BASE_URL}/market-data/audit/export",
            params={"format": export_format},
            timeout=15,
        )
        self._raise_for_status(response)
        return response.text

    def delete_market_data_sample(self, item_id: int) -> None:
        response = requests.delete(f"{API_BASE_URL}/market-data/samples/{item_id}", timeout=15)
        self._raise_for_status(response)

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
