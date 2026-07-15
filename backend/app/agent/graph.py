from __future__ import annotations

from typing import Any

from backend.app.agent.nodes import (
    check_required_fields_node,
    estimate_price_node,
    generate_listing_node,
    generate_question_node,
    search_similar_items_node,
    validate_price_node,
)
from backend.app.core.exceptions import AppError


class ReSaleAgentGraph:
    """轻量状态图封装，保留 LangGraph 节点边界，便于后续替换为真实 StateGraph。"""

    def prepare_next_question(self, state: dict[str, Any]) -> dict[str, Any]:
        check_required_fields_node(state)
        if state.get("missing_fields"):
            generate_question_node(state)
        return state

    def generate_listing(self, state: dict[str, Any]) -> dict[str, Any]:
        check_required_fields_node(state)
        if state.get("missing_fields"):
            raise AppError("商品信息还不完整，请先回答缺失字段", status_code=409, code="missing_required_fields")

        search_similar_items_node(state)
        estimate_price_node(state)
        validate_price_node(state)
        if state.get("price_validation_errors"):
            estimate_price_node(state)
            validate_price_node(state)
        if state.get("price_validation_errors"):
            raise AppError("价格校验失败：" + "；".join(state["price_validation_errors"]))

        generate_listing_node(state)
        return state

