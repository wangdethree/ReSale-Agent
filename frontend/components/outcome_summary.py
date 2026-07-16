from __future__ import annotations

from typing import Any

import streamlit as st


def render_outcome_summary(summary: dict[str, Any]) -> None:
    total_count = int(summary.get("total_count", 0))
    with st.expander("成交复盘", expanded=False):
        if total_count == 0:
            st.caption("暂无成交反馈")
            return

        cols = st.columns(2)
        cols[0].metric("成交数", total_count)
        cols[1].metric("符合比例", f"{float(summary.get('in_range_rate', 0)):.0%}")

        avg_delta = summary.get("average_delta_from_mid")
        avg_text = "暂无"
        if avg_delta is not None:
            sign = "+" if float(avg_delta) > 0 else ""
            avg_text = f"{sign}{float(avg_delta):.0f} 元"
        st.metric("平均偏差", avg_text)

        for item in summary.get("recent_outcomes", [])[:5]:
            delta = item.get("price_delta_from_mid")
            delta_text = "暂无偏差"
            if delta is not None:
                sign = "+" if float(delta) > 0 else ""
                delta_text = f"{sign}{float(delta):.0f} 元"
            st.write(
                f"- {item.get('product_label', '未命名')} · "
                f"{float(item.get('final_sold_price', 0)):.0f} 元 · "
                f"{item.get('price_position', '暂无')} · {delta_text}"
            )
