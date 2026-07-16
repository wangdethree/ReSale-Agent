from __future__ import annotations

from typing import Any


class ExportService:
    def build_markdown(self, state: dict[str, Any]) -> str:
        similar_lines = [
            self._build_similar_line(item)
            for item in state.get("similar_items", [])
        ]
        reason_lines = [f"- {reason}" for reason in state.get("price_reasons", [])]
        breakdown_lines = self._build_breakdown_lines(state.get("price_breakdown", {}))
        photo_lines = [f"- {item}" for item in state.get("photo_suggestions", [])]
        platform_lines = self._build_platform_lines(state.get("platform_copies", []))
        outcome_lines = self._build_outcome_lines(state.get("sale_outcome"))
        keyword_text = "、".join(state.get("keywords", []))

        return "\n".join(
            [
                f"# {state.get('title') or '出售方案'}",
                "",
                "## 估价建议",
                f"- 建议挂牌价：{state.get('listing_price', '未生成')} 元",
                f"- 合理成交区间：{state.get('deal_price_min', '未生成')}～{state.get('deal_price_max', '未生成')} 元",
                f"- 建议最低接受价：{state.get('suggested_floor_price', '未生成')} 元",
                f"- 估价置信度：{state.get('price_confidence', '未生成')}",
                "",
                "## 估价依据",
                *(reason_lines or ["- 暂无估价依据"]),
                "",
                "## 估价拆解",
                *(breakdown_lines or ["- 暂无估价拆解"]),
                "",
                "## 相似商品",
                *(similar_lines or ["- 未找到足够相似商品，当前结果仅为规则估价。"]),
                "",
                "## 出售文案",
                state.get("description") or "尚未生成文案。",
                "",
                "## 多平台文案",
                *(platform_lines or ["- 尚未生成多平台文案。"]),
                "",
                "## 成交反馈",
                *(outcome_lines or ["- 尚未记录成交反馈。"]),
                "",
                "## 搜索关键词",
                keyword_text or "暂无关键词",
                "",
                "## 瑕疵声明",
                state.get("defect_statement") or "暂无瑕疵声明。",
                "",
                "## 拍照建议",
                *(photo_lines or ["- 补充清晰照片后再发布。"]),
            ]
        )

    def _build_breakdown_lines(self, breakdown: dict[str, Any]) -> list[str]:
        if not breakdown:
            return []

        market_median = breakdown.get("market_median_price")
        market_text = f"{float(market_median):.0f} 元" if market_median is not None else "暂无"
        return [
            (
                f"- 原价 {float(breakdown.get('original_price', 0)):.0f} 元，"
                f"使用约 {breakdown.get('age_months', '未知')} 个月，"
                f"折旧系数 {float(breakdown.get('depreciation_factor', 0)):.2f}，"
                f"成色系数 {float(breakdown.get('condition_factor', 0)):.2f}。"
            ),
            (
                f"- 规则估价 {float(breakdown.get('rule_price', 0)):.0f} 元，"
                f"市场中位价 {market_text}，"
                f"最终基准价 {float(breakdown.get('base_price', 0)):.0f} 元。"
            ),
            (
                f"- 规则权重 {float(breakdown.get('rule_weight', 0)):.0%}，"
                f"相似成交权重 {float(breakdown.get('market_weight', 0)):.0%}，"
                f"相似样本 {breakdown.get('market_sample_count', 0)} 条。"
            ),
            (
                "- 图片线索："
                + (
                    f"已用于本地相似样本排序，最高相似度 {breakdown.get('image_similarity_max_score', 0)}。"
                    if breakdown.get("image_similarity_used")
                    else "未使用或未命中本地图片线索。"
                )
            ),
        ]

    def _build_similar_line(self, item: dict[str, Any]) -> str:
        score = item.get("image_similarity_score")
        score_text = f"，图片相似度 {score}" if score else ""
        reasons = "；".join(item.get("match_reasons", []))
        reason_text = f"（{reasons}）" if reasons else ""
        return (
            f"- {item.get('brand', '')} {item.get('model', '')}："
            f"模拟成交价 {item.get('sold_price')} 元{score_text}，{item.get('description')}{reason_text}"
        )

    def _build_platform_lines(self, platform_copies: list[dict[str, Any]]) -> list[str]:
        lines: list[str] = []
        for copy in platform_copies:
            tags = "、".join(copy.get("tags", []))
            lines.extend(
                [
                    f"### {copy.get('platform_label') or copy.get('platform')}",
                    "",
                    f"标题：{copy.get('title', '')}",
                    "",
                    str(copy.get("body", "")),
                    "",
                    f"标签：{tags or '暂无标签'}",
                    "",
                ]
            )
        return lines

    def _build_outcome_lines(self, outcome: dict[str, Any] | None) -> list[str]:
        if not outcome:
            return []

        delta = outcome.get("price_delta_from_mid")
        delta_text = "暂无偏差"
        if delta is not None:
            sign = "+" if float(delta) > 0 else ""
            delta_text = f"{sign}{float(delta):.0f} 元"

        rate = outcome.get("price_delta_rate")
        rate_text = f"{float(rate):+.1%}" if rate is not None else "暂无比例"
        return [
            f"- 最终成交价：{float(outcome.get('final_sold_price', 0)):.0f} 元",
            f"- 成交渠道：{outcome.get('sold_channel') or '未填写'}",
            f"- 相对估价中点偏差：{delta_text}（{rate_text}）",
            f"- 估价区间位置：{outcome.get('price_position') or '暂无'}",
            f"- 备注：{outcome.get('sale_notes') or '无'}",
        ]
