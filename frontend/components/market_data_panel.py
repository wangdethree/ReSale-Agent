from __future__ import annotations

from typing import Any

import streamlit as st


SOURCE_TYPE_LABELS = {"seed": "内置模拟", "imported": "导入样本"}


def render_market_data_panel(samples: dict[str, Any]) -> tuple[dict[str, Any] | None, int | None]:
    import_payload: dict[str, Any] | None = None
    delete_id: int | None = None
    with st.expander("价格数据源", expanded=False):
        total = int(samples.get("total_count", 0))
        st.metric("样本数", total)
        by_source = samples.get("by_source_type", {})
        if by_source:
            st.write(
                "、".join(
                    f"{SOURCE_TYPE_LABELS.get(source_type, source_type)} {count}"
                    for source_type, count in by_source.items()
                )
            )

        source_name = st.text_input("来源名称", value="个人整理样本", key="market-data-source-name")
        uploaded = st.file_uploader("成交样本 CSV", type=["csv"], key="market-data-csv")
        st.caption("必填列：category、product_type、sold_price")
        if st.button("导入样本", disabled=uploaded is None):
            import_payload = {"file": uploaded, "source_name": source_name}

        items = samples.get("items", [])
        if items:
            st.write("最近样本")
            for item in items[:8]:
                source = SOURCE_TYPE_LABELS.get(item.get("source_type"), item.get("source_type"))
                brand_model = " ".join(
                    part for part in [item.get("brand"), item.get("model")] if part
                ) or item.get("product_type", "未命名")
                st.write(
                    f"- {brand_model} · {float(item.get('sold_price', 0)):.0f} 元 · "
                    f"{source} · {item.get('source_name', '')}"
                )

            deletable_items = [item for item in items if item.get("deletable")]
            delete_options = ["", *[str(item["id"]) for item in deletable_items]]
            selected_id = st.selectbox(
                "删除导入样本",
                delete_options,
                format_func=lambda value: "不删除" if not value else _sample_label(deletable_items, int(value)),
                key="market-data-delete-id",
            )
            if st.button("删除所选样本", disabled=not selected_id):
                delete_id = int(selected_id)
        else:
            st.caption("暂无样本")
    return import_payload, delete_id


def render_market_data_import_result(result: dict[str, Any]) -> None:
    st.success(
        f"导入 {result.get('imported_count', 0)} 条，"
        f"跳过 {result.get('skipped_count', 0)} 条，"
        f"错误 {result.get('error_count', 0)} 条。"
    )
    errors = result.get("errors", [])
    if errors:
        with st.expander("错误行", expanded=False):
            for error in errors:
                st.write(f"- 第 {error.get('row_number')} 行：{error.get('message')}")


def _sample_label(items: list[dict[str, Any]], item_id: int) -> str:
    item = next((candidate for candidate in items if int(candidate["id"]) == item_id), None)
    if item is None:
        return str(item_id)
    brand_model = " ".join(part for part in [item.get("brand"), item.get("model")] if part) or item.get("product_type")
    return f"{brand_model} · {float(item.get('sold_price', 0)):.0f} 元"
