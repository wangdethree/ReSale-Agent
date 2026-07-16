from __future__ import annotations

from typing import Any

import streamlit as st


CHANNEL_OPTIONS = ["闲鱼", "转转", "小红书", "线下", "其他"]


def render_outcome_panel(listing: dict[str, Any]) -> dict[str, Any] | None:
    outcome = listing.get("sale_outcome") or {}
    with st.expander("成交反馈", expanded=bool(outcome)):
        if outcome:
            cols = st.columns(3)
            cols[0].metric("最终成交价", f"{outcome['final_sold_price']:.0f} 元")
            cols[1].metric("成交渠道", outcome.get("sold_channel", "未填写"))
            cols[2].metric("区间位置", outcome.get("price_position", "暂无"))
            delta = outcome.get("price_delta_from_mid")
            if delta is not None:
                sign = "+" if float(delta) > 0 else ""
                st.write(f"相对估价中点：{sign}{float(delta):.0f} 元")

        default_price = float(outcome.get("final_sold_price") or listing["price"]["deal_price_min"])
        default_channel = outcome.get("sold_channel") or CHANNEL_OPTIONS[0]
        default_index = CHANNEL_OPTIONS.index(default_channel) if default_channel in CHANNEL_OPTIONS else 0

        with st.form("sale-outcome-form"):
            final_sold_price = st.number_input("最终成交价", min_value=0.0, value=default_price, step=1.0)
            sold_channel = st.selectbox("成交渠道", CHANNEL_OPTIONS, index=default_index)
            sale_notes = st.text_area("备注", value=outcome.get("sale_notes", ""), height=90)
            submitted = st.form_submit_button("保存成交反馈")

        if not submitted:
            return None
        return {
            "final_sold_price": final_sold_price,
            "sold_channel": sold_channel,
            "sale_notes": sale_notes,
        }
