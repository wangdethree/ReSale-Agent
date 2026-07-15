from __future__ import annotations

from typing import Any

import streamlit as st


def render_confirmation_form(product: dict[str, Any], category: str) -> dict[str, Any]:
    st.subheader("确认识别结果")
    st.caption("识别结果只作为初稿，发布前应以你的确认为准。")
    with st.form("confirm_product_form"):
        product_type = st.text_input("商品类型", value=product.get("product_type") or "")
        brand = st.text_input("品牌", value=product.get("brand") or "")
        model = st.text_input("型号 / 版本 / ISBN", value=product.get("model") or "")
        color = st.text_input("颜色", value=product.get("color") or "")
        condition = st.selectbox(
            "外观状态",
            ["接近全新", "轻微使用痕迹", "明显使用痕迹", "存在明显瑕疵"],
            index=_condition_index(product.get("visible_condition")),
        )
        defects_text = st.text_area(
            "可见瑕疵",
            value="\n".join(product.get("visible_defects") or []),
            placeholder="每行写一条，没有可留空。",
        )
        confidence = st.slider(
            "模型置信度",
            min_value=0.0,
            max_value=1.0,
            value=float(product.get("vision_confidence") or 0.5),
            step=0.01,
        )
        submitted = st.form_submit_button("确认并进入补充信息")
    if not submitted:
        return {}
    return {
        "category": category,
        "product_type": product_type or None,
        "brand": brand or None,
        "model": model or None,
        "color": color or None,
        "visible_condition": condition,
        "visible_defects": [line.strip() for line in defects_text.splitlines() if line.strip()],
        "vision_confidence": confidence,
    }


def _condition_index(value: str | None) -> int:
    options = ["接近全新", "轻微使用痕迹", "明显使用痕迹", "存在明显瑕疵"]
    if value in options:
        return options.index(value)
    return 1

