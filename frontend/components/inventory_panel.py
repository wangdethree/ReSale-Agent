from __future__ import annotations

from typing import Any

import streamlit as st


INVENTORY_STATUS_LABELS = {
    "draft": "草稿",
    "ready": "待发布",
    "listed": "已发布",
    "sold": "已成交",
    "archived": "已归档",
}


def render_inventory_summary(summary: dict[str, Any]) -> None:
    with st.expander("库存总览", expanded=False):
        total = int(summary.get("total_count", 0))
        if not total:
            st.caption("暂无库存记录")
            return
        st.metric("库存项", total)
        by_status = summary.get("by_status", {})
        if by_status:
            st.write("状态分布")
            for status, count in by_status.items():
                st.write(f"- {INVENTORY_STATUS_LABELS.get(status, status)}：{count}")
        st.write("最近库存")
        for item in summary.get("items", [])[:5]:
            action = item.get("next_action") or "暂无动作"
            price = item.get("listing_price")
            price_text = f"{float(price):.0f} 元" if price is not None else "未估价"
            st.write(
                f"- {item.get('product_label', '未命名')} · "
                f"{INVENTORY_STATUS_LABELS.get(item.get('inventory_status'), item.get('inventory_status'))} · "
                f"{price_text} · {action}"
            )


def render_inventory_panel(listing: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    inventory_payload: dict[str, Any] | None = None
    performance_payload: dict[str, Any] | None = None
    with st.expander("库存和发布表现", expanded=bool(listing.get("listing_performance"))):
        current_status = listing.get("inventory_status", "ready")
        st.caption(f"当前状态：{INVENTORY_STATUS_LABELS.get(current_status, current_status)}")
        suggestion = listing.get("reprice_suggestion") or {}
        if suggestion:
            cols = st.columns(3)
            cols[0].metric("调价动作", suggestion.get("next_action", "暂无"))
            cols[1].metric("建议挂牌", f"{float(suggestion.get('recommended_listing_price', 0)):.0f} 元")
            cols[2].metric("价格变化", f"{float(suggestion.get('price_delta', 0)):+.0f} 元")
            st.write(suggestion.get("reason", ""))

        status_keys = list(INVENTORY_STATUS_LABELS.keys())
        status_index = status_keys.index(current_status) if current_status in status_keys else 1
        with st.form("inventory-status-form"):
            inventory_status = st.selectbox(
                "库存状态",
                status_keys,
                index=status_index,
                format_func=lambda value: INVENTORY_STATUS_LABELS[value],
            )
            storage_location = st.text_input("存放位置", value=listing.get("storage_location") or "")
            inventory_notes = st.text_area("库存备注", value=listing.get("inventory_notes") or "", height=70)
            if st.form_submit_button("保存库存状态"):
                inventory_payload = {
                    "inventory_status": inventory_status,
                    "storage_location": storage_location,
                    "inventory_notes": inventory_notes,
                }

        performance = listing.get("listing_performance") or {}
        with st.form("listing-performance-form"):
            cols = st.columns(4)
            days_listed = cols[0].number_input("发布天数", min_value=0, value=int(performance.get("days_listed", 0)), step=1)
            view_count = cols[1].number_input("浏览量", min_value=0, value=int(performance.get("view_count", 0)), step=1)
            favorite_count = cols[2].number_input("收藏量", min_value=0, value=int(performance.get("favorite_count", 0)), step=1)
            inquiry_count = cols[3].number_input("咨询量", min_value=0, value=int(performance.get("inquiry_count", 0)), step=1)
            current_listing_price = st.number_input(
                "当前挂牌价",
                min_value=0.0,
                value=float(performance.get("current_listing_price") or listing["price"]["listing_price"]),
                step=1.0,
            )
            if st.form_submit_button("生成表现调价建议"):
                performance_payload = {
                    "days_listed": int(days_listed),
                    "view_count": int(view_count),
                    "favorite_count": int(favorite_count),
                    "inquiry_count": int(inquiry_count),
                    "current_listing_price": float(current_listing_price),
                }
    return inventory_payload, performance_payload
