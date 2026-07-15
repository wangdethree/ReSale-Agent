from __future__ import annotations

from typing import Any

import streamlit as st


def render_negotiation_panel(default_floor_price: float | None) -> tuple[str, float | None, bool]:
    st.subheader("模拟议价")
    floor = st.number_input(
        "我的最低接受价",
        min_value=0.0,
        value=float(default_floor_price or 0),
        step=1.0,
    )
    buyer_message = st.text_input("买家消息", placeholder="例如：150 包邮行不行")
    submitted = st.button("生成建议回复")
    return buyer_message, floor, submitted


def render_negotiation_result(result: dict[str, Any]) -> None:
    st.write("买家意图：", result["buyer_intent"])
    st.write("是否低于最低价：", "是" if result["below_floor_price"] else "否")
    st.text_area("建议回复", value=result["suggested_reply"], height=120)
    st.write("下一步策略：", result["next_strategy"])

