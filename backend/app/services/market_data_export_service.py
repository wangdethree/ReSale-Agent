from __future__ import annotations

import csv
from io import StringIO
from typing import Any


ACTION_LABELS = {
    "import": "导入",
    "update": "更新",
    "disable": "停用",
    "restore": "恢复",
    "delete": "删除",
}


class MarketDataExportService:
    def build_audit_csv(self, events: list[dict[str, Any]]) -> str:
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "event_id",
                "item_id",
                "action",
                "action_label",
                "category",
                "product_type",
                "brand",
                "model",
                "source_name",
                "source_type",
                "created_at",
                "summary",
            ],
        )
        writer.writeheader()
        for event in events:
            writer.writerow(
                {
                    "event_id": event.get("id"),
                    "item_id": event.get("item_id"),
                    "action": event.get("action"),
                    "action_label": ACTION_LABELS.get(event.get("action"), event.get("action")),
                    "category": event.get("category") or "",
                    "product_type": event.get("product_type") or "",
                    "brand": event.get("brand") or "",
                    "model": event.get("model") or "",
                    "source_name": event.get("source_name") or "",
                    "source_type": event.get("source_type") or "",
                    "created_at": event.get("created_at") or "",
                    "summary": self._summarize_event(event),
                }
            )
        return output.getvalue()

    def build_audit_markdown(self, events: list[dict[str, Any]]) -> str:
        lines = [
            "# 价格样本审计记录",
            "",
            "| 时间 | 动作 | 商品 | 来源 | 摘要 |",
            "| --- | --- | --- | --- | --- |",
        ]
        for event in events:
            product = self._product_label(event)
            action = ACTION_LABELS.get(event.get("action"), event.get("action", "操作"))
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(event.get("created_at") or ""),
                        str(action),
                        self._escape_markdown(product),
                        self._escape_markdown(str(event.get("source_name") or "")),
                        self._escape_markdown(self._summarize_event(event)),
                    ]
                )
                + " |"
            )
        if not events:
            lines.append("|  | 暂无 |  |  | 暂无审计记录 |")
        return "\n".join(lines) + "\n"

    def _summarize_event(self, event: dict[str, Any]) -> str:
        detail = event.get("detail") or {}
        action = event.get("action")
        if action == "import":
            after = detail.get("after") or {}
            return f"导入成交价 {after.get('sold_price', event.get('sold_price', ''))} 元样本"
        if action == "disable":
            return "停用样本，不再参与估价检索"
        if action == "restore":
            return "恢复样本，重新参与估价检索"
        if action == "delete":
            return "删除导入样本，保留审计快照"
        if action == "update":
            after = detail.get("after") or {}
            note = after.get("user_notes") or "更新样本备注"
            return str(note)
        return "记录样本操作"

    def _product_label(self, event: dict[str, Any]) -> str:
        parts = [
            str(event.get("brand") or "").strip(),
            str(event.get("model") or "").strip(),
        ]
        label = " ".join(part for part in parts if part).strip()
        return label or str(event.get("product_type") or "价格样本")

    def _escape_markdown(self, value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")
