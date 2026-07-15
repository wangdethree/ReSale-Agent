from __future__ import annotations

import json
import logging
import os
import tempfile
import warnings
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_CASES_PATH = PROJECT_ROOT / "data" / "demo_cases.json"


def load_demo_cases() -> list[dict[str, Any]]:
    with DEMO_CASES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def run_case(client: TestClient, case: dict[str, Any]) -> dict[str, Any]:
    created = client.post("/api/v1/sessions", json={"category": case["category"]})
    created.raise_for_status()
    session_id = created.json()["session_id"]

    confirmed = client.post(
        f"/api/v1/sessions/{session_id}/confirm",
        json={"product": case["product"]},
    )
    confirmed.raise_for_status()

    question = client.get(f"/api/v1/sessions/{session_id}/questions/next")
    question.raise_for_status()
    if not question.json()["completed"]:
        raise RuntimeError(f"{case['name']} 仍有缺失字段：{question.json()['missing_fields']}")

    listing = client.post(f"/api/v1/sessions/{session_id}/listing/generate")
    listing.raise_for_status()
    listing_json = listing.json()
    floor_price = listing_json["price"]["suggested_floor_price"]

    negotiation = client.post(
        f"/api/v1/sessions/{session_id}/negotiation/reply",
        json={"buyer_message": case["buyer_message"], "user_floor_price": floor_price},
    )
    negotiation.raise_for_status()

    exported = client.get(f"/api/v1/sessions/{session_id}/export")
    exported.raise_for_status()

    return {
        "name": case["name"],
        "title": listing_json["title"],
        "listing_price": listing_json["price"]["listing_price"],
        "deal_range": f"{listing_json['price']['deal_price_min']}～{listing_json['price']['deal_price_max']}",
        "floor_price": floor_price,
        "buyer_intent": negotiation.json()["buyer_intent"],
        "report_chars": len(exported.text),
    }


def main() -> None:
    # 使用临时数据库，避免演示脚本污染本地开发数据。
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["RESALE_AGENT_DB_PATH"] = str(Path(temp_dir) / "resale.db")
        os.environ["RESALE_AGENT_UPLOAD_DIR"] = str(Path(temp_dir) / "uploads")

        warnings.filterwarnings("ignore", message="Using `httpx` with `starlette.testclient` is deprecated.*")
        from fastapi.testclient import TestClient

        from backend.app.main import app

        logging.getLogger("httpx").setLevel(logging.WARNING)
        with TestClient(app) as client:
            for case in load_demo_cases():
                result = run_case(client, case)
                print(
                    f"{result['name']} | {result['title']} | "
                    f"挂牌 {result['listing_price']} 元 | 成交 {result['deal_range']} 元 | "
                    f"最低 {result['floor_price']} 元 | 意图 {result['buyer_intent']} | "
                    f"报告 {result['report_chars']} 字"
                )


if __name__ == "__main__":
    main()
