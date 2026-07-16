from __future__ import annotations

from typing import Any

import streamlit as st


def _format_money(value: Any) -> str:
    if value is None:
        return "暂无"
    return f"{float(value):.0f} 元"


def _format_percent(value: Any) -> str:
    if value is None:
        return "暂无"
    return f"{float(value) * 100:.0f}%"


def _format_effect(value: Any) -> str:
    amount = float(value or 0)
    sign = "+" if amount > 0 else ""
    return f"{sign}{amount:.0f} 元"


def _render_price_breakdown(price: dict[str, Any]) -> None:
    breakdown = price.get("price_breakdown") or {}
    if not breakdown:
        return

    st.markdown("#### 估价拆解")
    cols = st.columns(3)
    cols[0].metric("规则估价", _format_money(breakdown.get("rule_price")))
    cols[1].metric("市场中位价", _format_money(breakdown.get("market_median_price")))
    cols[2].metric("最终基准价", _format_money(breakdown.get("base_price")))

    st.write(
        "- "
        f"原价 {_format_money(breakdown.get('original_price'))}，"
        f"使用约 {breakdown.get('age_months', '未知')} 个月，"
        f"折旧系数 {_format_percent(breakdown.get('depreciation_factor'))}，"
        f"成色系数 {_format_percent(breakdown.get('condition_factor'))}。"
    )
    st.write(
        "- "
        f"规则权重 {_format_percent(breakdown.get('rule_weight'))}，"
        f"相似成交权重 {_format_percent(breakdown.get('market_weight'))}，"
        f"相似样本 {breakdown.get('market_sample_count', 0)} 条。"
    )
    _render_adjustment_steps(breakdown.get("adjustment_steps", []))


def _render_adjustment_steps(steps: list[dict[str, Any]]) -> None:
    if not steps:
        return

    st.markdown("#### 调价明细")
    st.dataframe(
        [
            {
                "步骤": step.get("label", ""),
                "影响": _format_effect(step.get("effect")),
                "阶段价": _format_money(step.get("amount")),
                "说明": step.get("note", ""),
            }
            for step in steps
        ],
        use_container_width=True,
        hide_index=True,
    )


def _render_platform_copies(platform_copies: list[dict[str, Any]]) -> None:
    if not platform_copies:
        return

    st.markdown("#### 多平台文案")
    tabs = st.tabs([item.get("platform_label", item.get("platform", "平台")) for item in platform_copies])
    for tab, item in zip(tabs, platform_copies, strict=False):
        with tab:
            st.text_input(
                "标题",
                value=item.get("title", ""),
                key=f"platform-title-{item.get('platform')}",
            )
            st.text_area(
                "正文",
                value=item.get("body", ""),
                height=180,
                key=f"platform-body-{item.get('platform')}",
            )
            st.write("标签：", "、".join(item.get("tags", [])))


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
    _render_price_breakdown(price)

    st.markdown("#### 相似商品")
    for item in listing["similar_items"]:
        score = item.get("image_similarity_score")
        score_text = f"，图片相似度 {score}" if score else ""
        reasons = "；".join(item.get("match_reasons", []))
        reason_text = f"（{reasons}）" if reasons else ""
        st.write(
            f"- {item['brand']} {item['model']}：模拟成交价 {item['sold_price']} 元{score_text}，"
            f"{item['description']}{reason_text}"
        )

    st.markdown("#### 文案")
    st.text_input("标题", value=listing["title"])
    st.text_area("描述", value=listing["description"], height=180)
    st.write("关键词：", "、".join(listing["keywords"]))
    st.write(listing["defect_statement"])
    _render_platform_copies(listing.get("platform_copies", []))

    st.markdown("#### 拍照建议")
    for suggestion in listing["photo_suggestions"]:
        st.write(f"- {suggestion}")

    with st.expander("Agent 执行轨迹"):
        for item in listing.get("trace", []):
            status = "成功" if item.get("success") else "失败"
            st.write(f"{item.get('node')} · {status} · {item.get('duration_ms')} ms")
