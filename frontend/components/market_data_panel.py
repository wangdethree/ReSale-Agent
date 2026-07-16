from __future__ import annotations

from typing import Any

import streamlit as st


SOURCE_TYPE_LABELS = {"seed": "内置模拟", "imported": "导入样本"}
ACTIVE_LABELS = {"active": "启用", "inactive": "停用"}
ACTION_LABELS = {
    "import": "导入",
    "update": "更新",
    "disable": "停用",
    "restore": "恢复",
    "delete": "删除",
}


def render_market_data_panel(
    samples: dict[str, Any],
    audit: dict[str, Any],
    audit_csv: str,
    audit_markdown: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, int | None]:
    import_payload: dict[str, Any] | None = None
    update_payload: dict[str, Any] | None = None
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
        by_active = samples.get("by_active", {})
        if by_active:
            st.caption(
                "、".join(
                    f"{ACTIVE_LABELS.get(status, status)} {count}"
                    for status, count in by_active.items()
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
                    f"{source} · {_status_label(item)} · {item.get('source_name', '')}"
                )

            editable_items = [item for item in items if item.get("editable")]
            edit_options = ["", *[str(item["id"]) for item in editable_items]]
            selected_edit_id = st.selectbox(
                "管理导入样本",
                edit_options,
                format_func=lambda value: "不管理" if not value else _sample_label(editable_items, int(value)),
                key="market-data-edit-id",
            )
            if selected_edit_id:
                selected_item = _find_sample(editable_items, int(selected_edit_id))
                if selected_item:
                    with st.form("market-data-edit-form"):
                        active = st.checkbox("参与估价检索", value=bool(selected_item.get("active", True)))
                        user_notes = st.text_area(
                            "样本备注",
                            value=selected_item.get("user_notes") or "",
                            height=70,
                        )
                        cols = st.columns(2)
                        if cols[0].form_submit_button("保存状态"):
                            update_payload = {
                                "item_id": int(selected_edit_id),
                                "active": active,
                                "user_notes": user_notes,
                            }
                        if cols[1].form_submit_button("删除样本"):
                            delete_id = int(selected_edit_id)
        else:
            st.caption("暂无样本")

        events = audit.get("items", [])
        if events:
            st.write("最近操作")
            for event in events[:6]:
                st.caption(_audit_label(event))
            cols = st.columns(2)
            cols[0].download_button(
                "导出 CSV",
                audit_csv,
                file_name="market-data-audit.csv",
                mime="text/csv",
                key="market-data-audit-csv",
            )
            cols[1].download_button(
                "导出 Markdown",
                audit_markdown,
                file_name="market-data-audit.md",
                mime="text/markdown",
                key="market-data-audit-md",
            )
    return import_payload, update_payload, delete_id


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
    item = _find_sample(items, item_id)
    if item is None:
        return str(item_id)
    brand_model = " ".join(part for part in [item.get("brand"), item.get("model")] if part) or item.get("product_type")
    return f"{brand_model} · {float(item.get('sold_price', 0)):.0f} 元"


def _find_sample(items: list[dict[str, Any]], item_id: int) -> dict[str, Any] | None:
    return next((candidate for candidate in items if int(candidate["id"]) == item_id), None)


def _status_label(item: dict[str, Any]) -> str:
    return "启用" if item.get("active", True) else "停用"


def _audit_label(event: dict[str, Any]) -> str:
    action = ACTION_LABELS.get(event.get("action"), event.get("action", "操作"))
    brand_model = " ".join(part for part in [event.get("brand"), event.get("model")] if part)
    product = brand_model or event.get("product_type") or "价格样本"
    created_at = str(event.get("created_at") or "")[:16]
    return f"{created_at} · {action} · {product} · {event.get('source_name') or '本地样本'}"
