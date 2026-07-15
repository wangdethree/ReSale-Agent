from __future__ import annotations

from typing import Any

import streamlit as st


def render_listing(listing: dict[str, Any]) -> None:
    st.subheader("出售方案")
    price = listing["price"]
    cols = st.columns(4)
    cols[0].metric("建议挂牌价", f"{price['listing_price']} 元")
    cols[1].metric("成交区间", f"{price['deal_price_min']}～{price['deal_price_max']} 元")
    cols[2].metric("最低接受价", f"{price['suggested_floor_price']} 元")
    cols[3].metric("置信度", price["price_confidence"])

    st.markdown("#### 估价依据")
    for reason in price["price_reasons"]:
        st.write(f"- {reason}")

    st.markdown("#### 相似商品")
    for item in listing["similar_items"]:
        st.write(f"- {item['brand']} {item['model']}：模拟成交价 {item['sold_price']} 元，{item['description']}")

    st.markdown("#### 文案")
    st.text_input("标题", value=listing["title"])
    st.text_area("描述", value=listing["description"], height=180)
    st.write("关键词：", "、".join(listing["keywords"]))
    st.write(listing["defect_statement"])

    st.markdown("#### 拍照建议")
    for suggestion in listing["photo_suggestions"]:
        st.write(f"- {suggestion}")

    with st.expander("Agent 执行轨迹"):
        for item in listing.get("trace", []):
            status = "成功" if item.get("success") else "失败"
            st.write(f"{item.get('node')} · {status} · {item.get('duration_ms')} ms")

